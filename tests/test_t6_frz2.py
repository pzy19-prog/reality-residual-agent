from dataclasses import replace
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from rra.evidence import episode as episode_module
from rra.fast import Corrector
from rra.llm.adapter import HypothesisProposer, proposal_request
from rra.llm.providers import ReplayProvider, finalize_payload, request_sha256
from rra.s2.dsl import Action, Primitive
from rra.s2.fitter import CommandFeedback, Observation
from rra.sim import WorldConfig

REPO = Path(__file__).resolve().parents[1]


def _ambiguous_pause():
    return {"action": Action.PAUSE_AND_REOBSERVE, "action_time": None,
            "faults": (), "passing": [], "fits": [], "verifications": [],
            "gate_reason": "AMBIGUOUS"}


class _CountingProposer:
    def __init__(self):
        self.calls = 0

    def propose(self, evidence_packet, context_text="", *, s2_summary=None):
        self.calls += 1
        return SimpleNamespace(items=[], error=None, receipt={"unknown_ids": []})


def _run_with_hold(monkeypatch, variant):
    calls = []
    original = Corrector.correct

    def escalate_once(self, plan, residual, disturbance, nominal_speed):
        result = original(self, plan, residual, disturbance, nominal_speed)
        if plan.observation_time == 0.0:
            return replace(result, reason="ESCALATE: test")
        return result

    def pause(observations, **kwargs):
        calls.append(kwargs["current_time"])
        return _ambiguous_pause()

    monkeypatch.setattr(Corrector, "correct", escalate_once)
    monkeypatch.setattr(episode_module, "run_b3", pause)
    config = WorldConfig(scenario="nominal", object_count=1,
                         initial_position_min=-3.0, initial_position_max=-3.0,
                         episode_steps=40)
    proposer = _CountingProposer() if variant != "B3" else None
    receipt = episode_module.run_episode(config, 4, True, system2_enabled=True,
                                         s2_variant=variant, proposer=proposer)
    return calls, receipt, proposer


@pytest.mark.parametrize("variant", ["B4_STRICT", "B4_TIEBREAK"])
def test_b4_variants_enter_and_exhaust_reobserve_hold_like_b3(monkeypatch, variant):
    b3_calls, b3_receipt, _ = _run_with_hold(monkeypatch, "B3")
    monkeypatch.undo()
    calls, receipt, proposer = _run_with_hold(monkeypatch, variant)
    assert calls[:2] == [0.0, 0.5]
    assert calls == b3_calls
    assert receipt["system2_reobserve"] == b3_receipt["system2_reobserve"]
    assert receipt["system2_reobserve"]["end_reasons"]["window_end"] == 1
    assert receipt["evaluator_objects"][0]["command_issued"] is False
    assert receipt["outcomes"][0]["status"] == "escalated"
    assert receipt["outcomes"][0]["reason"].endswith(";REOBSERVE_EXHAUSTED")
    assert proposer.calls == len(calls)
    if variant == "B4_TIEBREAK":
        assert {d["gate_reason"] for d in receipt["system2_decisions"]} == {
            "TIEBREAK_FALLBACK:NO_PROPOSED_PASSING_STRUCTURE"}
    assert {d["action"] for d in receipt["system2_decisions"]} == {Action.PAUSE_AND_REOBSERVE.value}


def _patched_fit(monkeypatch, objective_by_call):
    import rra.s2.fitter as fitter
    calls = 0

    def fake_linear_fit(A, y):
        nonlocal calls
        objective = objective_by_call(calls)
        calls += 1
        return np.zeros(A.shape[1]), np.array([objective ** 0.5, 0, 0, 0, 0, 0])

    monkeypatch.setattr(fitter, "_linear_fit", fake_linear_fit)
    return fitter


def test_actuator_delay_fit_chooses_smallest_delay_within_tie_tolerance(monkeypatch):
    fitter = _patched_fit(monkeypatch, lambda k: 1.0 + 5e-13 if k == 5 else 1.0)
    obs = [Observation(i * .1, 0.0, 0.0) for i in range(6)]
    feedback = [CommandFeedback(1.0, 1.055, True, True)]
    result = fitter.fit((Primitive.ACTUATOR_DELAY,), obs, nominal_speed=1.0, feedback=feedback)
    assert result.parameters["actuator_delay"] == pytest.approx(0.05, abs=1e-12)


def test_actuator_delay_fit_without_tie_keeps_strict_minimum(monkeypatch):
    fitter = _patched_fit(monkeypatch, lambda k: 1.0 + 1e-9 if k == 5 else 1.0)
    obs = [Observation(i * .1, 0.0, 0.0) for i in range(6)]
    feedback = [CommandFeedback(1.0, 1.055, True, True)]
    result = fitter.fit((Primitive.ACTUATOR_DELAY,), obs, nominal_speed=1.0, feedback=feedback)
    assert result.parameters["actuator_delay"] == pytest.approx(0.06, abs=1e-12)


def test_speed_step_delay_tie_selects_lexicographic_smallest_tau_then_delay(monkeypatch):
    objective = {6: 1.0 + 5e-13, 56: 1.0}
    fitter = _patched_fit(monkeypatch, lambda k: objective.get(k, 2.0))
    obs = [Observation(i * .1, 0.0, 0.0) for i in range(6)]
    feedback = [CommandFeedback(1.0, 1.055, True, True)]
    result = fitter.fit((Primitive.SPEED_STEP, Primitive.ACTUATOR_DELAY), obs,
                        nominal_speed=1.0, feedback=feedback)
    assert result.parameters["speed_step_time"] == pytest.approx(0.5, abs=1e-12)
    assert result.parameters["actuator_delay"] == pytest.approx(0.06, abs=1e-12)


_DRIVER = r"""
import sys
from pathlib import Path
import rra.eval.b4_dev as b4_dev
from rra import cli
b4_dev.ROOT = Path(sys.argv[1])
raise SystemExit(cli.main(["s2-b4-dev", "--replay", "--subset", "--nproc", "1",
                           "--output-dir", sys.argv[2]]))
"""


def test_s2_b4_dev_replay_cache_miss_exits_nonzero_without_artifact(tmp_path):
    root = tmp_path / "root"
    (root / "config").mkdir(parents=True)
    (root / "artifacts" / "s2").mkdir(parents=True)
    (root / "artifacts" / "llm_cache").mkdir(parents=True)
    (root / "config" / "dev_seeds.json").write_text((REPO / "config" / "dev_seeds.json").read_text())
    (root / "artifacts" / "s2" / "diag-d1g.json").write_text(json.dumps({"seeds": [21]}))
    out = tmp_path / "out"
    env = {k: v for k, v in os.environ.items() if k not in ("NVIDIA_API_KEY", "ZETARIS_TOKEN")}
    env["PYTHONPATH"] = str(REPO / "src")
    proc = subprocess.run([sys.executable, "-c", _DRIVER, str(root), str(out)],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
    assert proc.returncode != 0
    assert "ReplayCacheMiss" in proc.stderr
    assert not (out / "b4-dev.json").exists()


def test_finalized_request_floats_are_six_decimal_fixed_points():
    settings = ReplayProvider("unused").settings
    payload = finalize_payload(proposal_request(
        {"observations": [{"time": 0.1, "observed_x": -4.795738613622927,
                           "nominal_x": -4.775529644730117}],
         "feedback": []},
        {"passing": [{"structure_id": "SENSOR_BIAS", "rmse": -0.04795738613622927, "n_usable": 10}],
         "current_time": 0.9, "horizon": 9.9},
    ), settings)
    user = json.loads(payload["messages"][1]["content"])
    values = list(_floats(user))
    assert values
    assert all(round(value, 6) == value for value in values)


def test_request_body_and_cache_key_ignore_float_changes_beyond_six_places():
    settings = ReplayProvider("unused").settings
    left = proposal_request({"value": -4.795738613622927}, {"passing": []})
    right = proposal_request({"value": -4.795738613622926}, {"passing": []})
    first = finalize_payload(left, settings)
    second = finalize_payload(right, settings)
    assert first == second
    assert request_sha256(first) == request_sha256(second)


def _floats(value):
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _floats(item)
    elif isinstance(value, list):
        for item in value:
            yield from _floats(item)


def test_b4_episode_provider_payload_floats_are_rounded_to_six_places():
    from rra.eval.b4_dev import _realization
    from rra.eval.context_v3 import freeze_episode_contexts
    from rra.eval.framework import v3_world_config
    from rra.evidence import run_episode

    seeds = json.loads((REPO / "config/dev_seeds.json").read_text())["seeds"]
    seed = 21
    realization = _realization(seeds.index(seed), seed)
    frozen = freeze_episode_contexts(str(seed), seed,
                                    realization.fault_family or realization.structure)["NO_TEXT_CONTEXT"]

    class CaptureFinalizedProvider:
        def __init__(self):
            self.bodies = []

        def complete(self, body):
            payload = finalize_payload(body, ReplayProvider("unused").settings)
            self.bodies.append(payload)
            return {"choices": [{"message": {"content": '{"items": []}'}}]}

    provider = CaptureFinalizedProvider()
    run_episode(v3_world_config("nominal"), seed, True, terminal_monitoring="corrected",
                realization=realization, text_context=frozen.text, system2_enabled=True,
                s2_variant="B4_STRICT", proposer=HypothesisProposer(provider))
    assert provider.bodies
    for body in provider.bodies:
        user = json.loads(body["messages"][1]["content"])
        assert set(user) == {"evidence_packet", "s2_summary"}
        values = list(_floats(user["evidence_packet"])) + list(_floats(user["s2_summary"]))
        assert values and all(round(value, 6) == value for value in values)
