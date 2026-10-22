from dataclasses import replace

from rra.evidence import episode as episode_module
from rra.fast import Corrector
from rra.s2.dsl import Action
from rra.sim import WorldConfig
from rra.eval.scenarios import EpisodeRealization


def _pause_result():
    return {
        "action": Action.PAUSE_AND_REOBSERVE, "action_time": None,
        "faults": (), "passing": [], "fits": [], "verifications": [],
        "gate_reason": "INSUFFICIENT_EVIDENCE",
    }


def test_unverified_pause_does_not_veto_fast_layer_command(monkeypatch):
    calls = []
    original_correct = Corrector.correct

    def force_first_infeasible(self, plan, residual, disturbance, nominal_speed):
        result = original_correct(self, plan, residual, disturbance, nominal_speed)
        if plan.observation_time == 0.0:
            return replace(result, infeasible=True)
        return result

    def pause_b3(observations, **kwargs):
        calls.append(len(observations))
        return _pause_result()

    monkeypatch.setattr(Corrector, "correct", force_first_infeasible)
    monkeypatch.setattr(episode_module, "run_b3", pause_b3)
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-0.15,
        initial_position_max=-0.15, episode_steps=90,
    )

    receipt = episode_module.run_episode(config, 17, True, system2_enabled=True)

    assert calls == [1]
    assert receipt["system2_decisions"][0]["action"] == Action.PAUSE_AND_REOBSERVE.value
    assert receipt["evaluator_objects"][0]["command_issued"] is True
    assert receipt["outcomes"][0]["status"] == "picked"
    assert receipt["system2_fault_vetoes"] == []


def test_sensor_stuck_positive_evidence_vetoes_and_is_receipted(monkeypatch):
    original_correct = Corrector.correct
    forced = False

    def trigger_s2_after_stuck_evidence(self, plan, residual, disturbance, nominal_speed):
        nonlocal forced
        result = original_correct(self, plan, residual, disturbance, nominal_speed)
        if not forced and plan.observation_time >= 0.8:
            forced = True
            return replace(result, infeasible=True)
        return result

    monkeypatch.setattr(Corrector, "correct", trigger_s2_after_stuck_evidence)
    realization = EpisodeRealization(
        (), {}, "SENSOR_STUCK", {"trigger_target": 0, "trigger_time": 0.3},
    )
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-3.0,
        initial_position_max=-3.0, episode_steps=90,
    )

    receipt = episode_module.run_episode(
        config, 19, True, system2_enabled=True, realization=realization,
    )

    assert receipt["system2_fault_vetoes"]
    veto = receipt["system2_fault_vetoes"][0]
    checks = {row["check_item"]: row["evidence_ids"] for row in veto["check_items"]}
    assert "SENSOR_STUCK" in checks
    assert len(checks["SENSOR_STUCK"]) == 4
    assert all(evidence_id.startswith("obs:0:") for evidence_id in checks["SENSOR_STUCK"])
    assert receipt["evaluator_objects"][0]["command_issued"] is False
    assert receipt["safe_stop"] is True
