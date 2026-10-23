from dataclasses import replace
from types import SimpleNamespace

from rra.evidence import episode as episode_module
from rra.fast import Corrector
from rra.s2.dsl import Action
from rra.s2.dsl import FaultHypothesis, Primitive
from rra.s2.fitter import Observation as S2Observation
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


def test_object_missing_latches_before_absence_escalation_and_vetoes_all_later_targets(monkeypatch):
    absent_branch_b3_calls = []
    def unexpected_b3(*args, **kwargs):
        absent_branch_b3_calls.append(True)
        raise AssertionError("hard fault latch must run before absent handling")
    monkeypatch.setattr(episode_module, "run_b3", unexpected_b3)
    realization = EpisodeRealization(
        (), {}, "OBJECT_MISSING", {"trigger_target": 0, "trigger_time": 0.2},
    )
    config = WorldConfig(
        scenario="nominal", object_count=3, initial_position_min=-3.0,
        initial_position_max=-3.0, episode_steps=90,
    )
    receipt = episode_module.run_episode(config, 91, True, system2_enabled=True,
                                         realization=realization)

    latch = receipt["system2_hard_fault_latch"]
    assert latch["latched"] is True
    assert latch["events"][0]["category"] == FaultHypothesis.OBJECT_MISSING_OR_DROPPED.value
    assert latch["events"][0]["evidence_ids"] == ["presence:0:0.200"]
    assert receipt["safe_stop"] is True
    assert all(not row["command_issued"] for row in receipt["evaluator_objects"])
    assert all(row["action"] == Action.HUMAN_ESCALATION.value
               for row in receipt["system2_decisions"])
    assert {row["target_id"] for row in receipt["system2_fault_vetoes"]} == {0, 1, 2}
    assert absent_branch_b3_calls == []


def test_empty_fault_window_still_latches_with_available_target_evidence(monkeypatch):
    def empty_window(*args, **kwargs):
        return ((FaultHypothesis.SENSOR_STUCK,),
                {FaultHypothesis.SENSOR_STUCK: []})

    monkeypatch.setattr(episode_module, "check_faults", empty_window)
    config = WorldConfig(scenario="nominal", object_count=1,
                         initial_position_min=-3.0, initial_position_max=-3.0,
                         episode_steps=40)

    receipt = episode_module.run_episode(config, 94, True, system2_enabled=True)

    assert receipt["system2_hard_fault_latch"]["latched"] is True
    assert receipt["system2_hard_fault_latch"]["events"][0]["evidence_ids"] == ["obs:0:0.000"]


def test_sensor_stuck_hard_latch_revokes_prior_authorization(monkeypatch):
    original_correct = Corrector.correct
    forced = False

    def trigger_s2(self, plan, residual, disturbance, nominal_speed):
        nonlocal forced
        result = original_correct(self, plan, residual, disturbance, nominal_speed)
        if not forced and plan.observation_time >= 0.5:
            forced = True
            return replace(result, infeasible=True)
        return result

    def authorize_model(observations, **kwargs):
        hypothesis = SimpleNamespace(
            hypothesis_id="constructed-offset", fitted_parameters={"velocity_offset": 0.0},
            rmse=0.0, structure=(Primitive.VELOCITY_OFFSET,), passed=True,
            n_usable=len(observations), residual_vector=(), violated_invariants=(),
            evidence_refs=(),
        )
        error = kwargs["error"]
        times = [round(kwargs["current_time"] + i * kwargs["dt"], 10)
                 for i in range(int((kwargs["horizon"] - kwargs["current_time"])
                                    / kwargs["dt"]) + 1)]
        action_time = min(times, key=lambda time: error(hypothesis, time))
        return {"action": Action.UPDATE_MODEL_AND_REPLAN, "action_time": action_time,
                "faults": (), "passing": [hypothesis], "fits": [],
                "verifications": [hypothesis], "gate_reason": "COMMON_ACTION"}

    def passing_fit(structure, observations, **kwargs):
        return SimpleNamespace(structure=tuple(structure), parameters={"velocity_offset": 0.0},
                               objective=0.0, residuals=(), n_usable=len(observations),
                               no_fit=False)

    def delayed_stuck_evidence(observations, **kwargs):
        if observations and observations[-1].time >= 1.0:
            return (FaultHypothesis.SENSOR_STUCK,)
        return (FaultHypothesis.UNKNOWN_OR_INSUFFICIENT_EVIDENCE,)

    monkeypatch.setattr(Corrector, "correct", trigger_s2)
    monkeypatch.setattr(episode_module, "run_b3", authorize_model)
    monkeypatch.setattr(episode_module, "fit_hypothesis", passing_fit)
    monkeypatch.setattr(episode_module, "check_faults", delayed_stuck_evidence)
    realization = EpisodeRealization((Primitive.SENSOR_BIAS.value,), {"sensor_bias": 1.5},
                                     "SENSOR_STUCK", {"trigger_target": 0, "trigger_time": 2.0})
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-3.0,
        initial_position_max=-3.0, episode_steps=90,
    )
    receipt = episode_module.run_episode(config, 92, True, system2_enabled=True,
                                         realization=realization)

    original_authorizations = [row for row in receipt["system2_decisions"]
                               if row.get("authorization") is not None]
    assert original_authorizations
    assert any(event.get("reason") == "HARD_FAULT_LATCH"
               for event in receipt["system2_authorization_events"])
    assert receipt["system2_hard_fault_latch"]["latched"] is True
    assert receipt["safe_stop"] is True
    assert receipt["evaluator_objects"][0]["command_issued"] is False


def test_sensor_spike_burst_does_not_latch_and_pause_can_recover(monkeypatch):
    original_correct = Corrector.correct
    forced = False

    def trigger_pause(self, plan, residual, disturbance, nominal_speed):
        nonlocal forced
        result = original_correct(self, plan, residual, disturbance, nominal_speed)
        if not forced:
            forced = True
            return replace(result, infeasible=True)
        return result

    def pause_b3(*args, **kwargs):
        return _pause_result()

    monkeypatch.setattr(Corrector, "correct", trigger_pause)
    monkeypatch.setattr(episode_module, "run_b3", pause_b3)
    realization = EpisodeRealization(
        (), {}, "SENSOR_SPIKE_BURST", {"trigger_target": 0, "trigger_time": 0.5,
                                         "duration_samples": 2, "magnitude": 1.5},
    )
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-0.15,
        initial_position_max=-0.15, episode_steps=90,
    )
    receipt = episode_module.run_episode(config, 93, True, system2_enabled=True,
                                         realization=realization)

    assert receipt["system2_hard_fault_latch"]["latched"] is False
    assert receipt["system2_decisions"][0]["action"] == Action.PAUSE_AND_REOBSERVE.value
    assert receipt["evaluator_objects"][0]["command_issued"] is True
