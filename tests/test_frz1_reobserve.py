from dataclasses import replace
import json
from pathlib import Path

from rra.evidence import episode as episode_module
from rra.eval.b3_dev import _run_seed
from rra.eval.framework import v3_world_config
from rra.fast import Corrector
from rra.s2.dsl import Action, FaultHypothesis
from rra.sim import WorldConfig


def _pause():
    return {"action": Action.PAUSE_AND_REOBSERVE, "action_time": None,
            "faults": (), "passing": [], "fits": [], "verifications": [],
            "gate_reason": "INSUFFICIENT_EVIDENCE"}


def test_escalated_target_is_reobserved_after_half_second_and_held_from_fast_commands(monkeypatch):
    calls = []
    original = Corrector.correct

    def escalate_once(self, plan, residual, disturbance, nominal_speed):
        result = original(self, plan, residual, disturbance, nominal_speed)
        if plan.observation_time == 0.0:
            return replace(result, reason="ESCALATE: test")
        return result

    def pause(observations, **kwargs):
        calls.append(kwargs["current_time"])
        return _pause()

    monkeypatch.setattr(Corrector, "correct", escalate_once)
    monkeypatch.setattr(episode_module, "run_b3", pause)
    config = WorldConfig(scenario="nominal", object_count=1,
                         initial_position_min=-3.0, initial_position_max=-3.0,
                         episode_steps=40)

    receipt = episode_module.run_episode(config, 4, True, system2_enabled=True)

    assert calls[:2] == [0.0, 0.5]
    assert receipt["system2_reobserve"]["end_reasons"]["window_end"] == 1
    assert receipt["evaluator_objects"][0]["command_issued"] is False
    assert receipt["outcomes"][0]["status"] == "escalated"
    assert receipt["outcomes"][0]["reason"].endswith(";REOBSERVE_EXHAUSTED")


def test_continuous_escalation_keeps_reobserving_until_window_end(monkeypatch):
    calls = []
    original = Corrector.correct

    def escalate_every_step(self, plan, residual, disturbance, nominal_speed):
        result = original(self, plan, residual, disturbance, nominal_speed)
        return replace(result, reason="ESCALATE: continuous test")

    def pause(observations, **kwargs):
        calls.append(kwargs["current_time"])
        return _pause()

    monkeypatch.setattr(Corrector, "correct", escalate_every_step)
    monkeypatch.setattr(episode_module, "run_b3", pause)
    config = WorldConfig(scenario="nominal", object_count=1,
                         initial_position_min=-3.0, initial_position_max=-3.0,
                         episode_steps=40)

    receipt = episode_module.run_episode(config, 6, True, terminal_monitoring="corrected",
                                         system2_enabled=True)

    assert calls == [i * 0.5 for i in range(len(calls))]
    assert len(calls) > 2
    assert receipt["system2_reobserve"]["end_reasons"]["window_end"] == 1
    assert receipt["system2_reobserve"]["end_reasons"]["s2_non_pause"] == 0
    assert receipt["system2_reobserve"]["reobservations"] == len(calls) - 1


def test_diag_dev_seed_reobservations_stay_within_retry_interval():
    seed_path = Path(__file__).parents[1] / "config" / "dev_seeds.json"
    seeds = json.loads(seed_path.read_text())["seeds"]
    dt = v3_world_config("nominal").dt
    checked_pairs = 0

    # Indices 1, 2, and 3 are members of the registered diag-d1g subset.
    for index in (1, 2, 3):
        result = _run_seed((index, seeds[index]))
        decisions_by_target = {}
        for decision in result.get("system2_decisions", []):
            decisions_by_target.setdefault(decision["target_id"], []).append(decision["time"])
        for times in decisions_by_target.values():
            for previous, current in zip(times, times[1:]):
                assert current - previous <= 0.5 + dt + 1e-9
                checked_pairs += 1

    assert checked_pairs > 0


def test_hard_fault_latch_ends_an_existing_reobserve_hold(monkeypatch):
    original = Corrector.correct
    first = True

    def escalate_once(self, plan, residual, disturbance, nominal_speed):
        nonlocal first
        result = original(self, plan, residual, disturbance, nominal_speed)
        if first:
            first = False
            return replace(result, reason="ESCALATE: test latch")
        return result

    checks = 0
    def fault_on_second_sample(*args, **kwargs):
        nonlocal checks
        checks += 1
        if checks == 1:
            return ((FaultHypothesis.UNKNOWN_OR_INSUFFICIENT_EVIDENCE,), {})
        if kwargs.get("return_windows"):
            return ((FaultHypothesis.SENSOR_STUCK,), {FaultHypothesis.SENSOR_STUCK: []})
        return (FaultHypothesis.SENSOR_STUCK,)

    monkeypatch.setattr(Corrector, "correct", escalate_once)
    monkeypatch.setattr(episode_module, "run_b3", lambda *a, **k: _pause())
    monkeypatch.setattr(episode_module, "check_faults", fault_on_second_sample)
    config = WorldConfig(scenario="nominal", object_count=1,
                         initial_position_min=-3.0, initial_position_max=-3.0,
                         episode_steps=40)

    receipt = episode_module.run_episode(config, 5, True, system2_enabled=True)

    assert receipt["system2_hard_fault_latch"]["latched"] is True
    assert receipt["outcomes"][0]["status"] == "escalated"
    assert receipt["outcomes"][0]["reason"].endswith(";REOBSERVE_EXHAUSTED")
    assert receipt["system2_reobserve"]["end_reasons"]["latch"] == 1
