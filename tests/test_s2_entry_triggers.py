from types import SimpleNamespace
from dataclasses import replace

from rra.controller import Controller, Execution
from rra.evidence import episode as episode_module
from rra.fast import Corrector
from rra.s2.dsl import Action, Primitive
from rra.s2.authorization import authorize
from rra.sim import WorldConfig
from rra.eval.b3_dev import _preservation_regression_sources, _unsafe_source_counts


def _pause_result():
    return {
        "action": Action.PAUSE_AND_REOBSERVE,
        "action_time": None,
        "faults": (),
        "passing": [],
        "fits": [],
        "verifications": [],
        "gate_reason": "NONE",
    }


def test_correction_infeasible_triggers_s2_before_command_window(monkeypatch):
    calls = []
    monkeypatch.setattr(episode_module, "run_b3", lambda *args, **kwargs: (calls.append(kwargs) or _pause_result()))
    config = WorldConfig(
        scenario="moving", moving_speed_delta=0.10, object_count=1,
        initial_position_min=-7.934, initial_position_max=-7.934,
    )

    receipt = episode_module.run_episode(config, 0, True, system2_enabled=True)

    assert any(row["infeasible"] for row in receipt["compensation_records"])
    assert calls
    command_window_start = (config.x_pick - config.initial_position_min) / config.belt_speed - config.dt / 2
    assert calls[0]["current_time"] < command_window_start
    assert receipt["outcomes"][0]["reason"] == "correction_infeasible"


def test_system2_disabled_receipt_matches_default_byte_for_byte():
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-0.15,
        initial_position_max=-0.15, episode_steps=90,
    )
    implicit = episode_module.run_episode(config, 7, True)
    disabled = episode_module.run_episode(config, 7, True, system2_enabled=False)

    assert implicit == disabled


def test_unsafe_source_split_sums_to_original_count():
    split = _unsafe_source_counts(
        [1, 2, 3],
        [
            {"target_id": 1, "authorization_source": "fast_layer_command"},
            {"target_id": 2, "authorization_source": "s2_authorized"},
            {"target_id": 3, "authorization_source": "fast_layer_command"},
        ],
    )

    assert split == {"fast_layer_command": 2, "s2_authorized": 1}
    assert sum(split.values()) == 3


def test_preservation_regressions_are_split_into_registered_causes():
    split = _preservation_regression_sources(
        [1, 2, 3],
        [
            {"target_id": 1, "authorization_source": "fast_layer_command"},
            {"target_id": 2, "authorization_source": "s2_authorized"},
            {"target_id": 3, "authorization_source": "fast_layer_command"},
        ],
        [{"target_id": 1}],
    )

    assert split == {"fault_veto": 1, "s2_authorized_action": 1, "other": 1}


def test_verified_action_without_policy_exception_is_a_noop(monkeypatch):
    original_correct = Corrector.correct
    forced = False

    def trigger_once(self, plan, residual, disturbance, nominal_speed):
        nonlocal forced
        result = original_correct(self, plan, residual, disturbance, nominal_speed)
        if not forced:
            forced = True
            return replace(result, infeasible=True)
        return result

    def verified_but_ordinary(observations, **kwargs):
        hypothesis = SimpleNamespace(
            hypothesis_id="ordinary-velocity-offset", fitted_parameters={"velocity_offset": 0.0},
            rmse=0.0, structure=(Primitive.VELOCITY_OFFSET,), passed=True,
            n_usable=len(observations), residual_vector=(), violated_invariants=(),
            evidence_refs=(),
        )
        return {"action": Action.UPDATE_MODEL_AND_REPLAN, "action_time": kwargs["current_time"],
                "faults": (), "passing": [hypothesis], "fits": [], "verifications": [hypothesis],
                "gate_reason": "COMMON_ACTION"}

    monkeypatch.setattr(Corrector, "correct", trigger_once)
    monkeypatch.setattr(episode_module, "run_b3", verified_but_ordinary)
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-0.15,
        initial_position_max=-0.15, episode_steps=90,
    )
    receipt = episode_module.run_episode(config, 21, True, system2_enabled=True)

    assert receipt["system2_decisions"][0]["action"] == Action.UPDATE_MODEL_AND_REPLAN.value
    assert receipt["system2_decisions"][0].get("authorization") is None
    assert receipt["evaluator_objects"][0]["authorization_source"] == "fast_layer_command"


def test_empty_exception_cannot_create_authorization():
    import pytest

    with pytest.raises(ValueError, match="non-empty temporary policy exception"):
        authorize(episode_id="1", hypothesis_id="h", evidence_ids=["e"], parameters={},
                  score=0.0, action=Action.UPDATE_MODEL_AND_REPLAN, scope="target:0",
                  expires_at=1.0, exception={})


def test_outcome_escalation_authorizes_then_revokes_after_failed_result(monkeypatch):
    s2_calls = []

    def authorized_b3(*args, **kwargs):
        s2_calls.append(kwargs)
        if len(s2_calls) > 1:
            return _pause_result()
        hypothesis = SimpleNamespace(
            hypothesis_id="constructed-velocity-offset", fitted_parameters={"velocity_offset": 0.0},
            rmse=0.0, structure=(), passed=True,
        )
        return {
            "action": Action.UPDATE_MODEL_AND_REPLAN, "action_time": 0.0,
            "faults": (), "passing": [hypothesis], "fits": [], "verifications": [hypothesis],
            "gate_reason": "COMMON",
        }

    monkeypatch.setattr(episode_module, "run_b3", authorized_b3)
    monkeypatch.setattr(
        Controller, "execute_2d",
        lambda self, command, actual_x, actual_y, actual_time: Execution(True, False, 1.0, "constructed miss"),
    )
    config = WorldConfig(
        scenario="nominal", object_count=5, initial_position_min=-7.0,
        initial_position_max=-7.0, episode_steps=90,
    )

    receipt = episode_module.run_episode(config, 3, True, system2_enabled=True)

    authorizations = receipt["system2_episode_authorizations"]
    assert s2_calls
    assert len(s2_calls[0]["feedback"]) >= 3
    assert receipt["evaluator_objects"][3]["command_issued"] is True
    assert authorizations[0]["authorization"]["terminal_condition"] == "next_authorized_failure_or_model_contradiction"
    assert authorizations[0]["target_revocations"]
    assert authorizations[0]["target_revocations"][0]["target_id"] == 3
    assert authorizations[0]["target_revocations"][0]["reason"] == "POST_VERIFICATION_CHANGE"
    assert any(row.get("reason") == "POST_VERIFICATION_CHANGE"
               for row in receipt["system2_authorization_events"])
