from dataclasses import replace

from rra.evidence import episode as episode_module
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
    assert receipt["evaluator_objects"][0]["command_issued"] is False
    assert receipt["outcomes"][0]["status"] == "escalated"
    assert receipt["outcomes"][0]["reason"].endswith(";REOBSERVE_EXHAUSTED")


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
