import pytest
from pydantic import ValidationError

from rra.evidence import run_episode
from rra.fast import Corrector
from rra.planner import Plan
from rra.sim import WorldConfig


def plan(eta=8.0, now=0.0):
    return Plan(target_id=0, expected_arrival_time=eta, pick_position=0.0, observation_time=now)


def test_world_config_rejects_unreachable_prediction_horizon():
    with pytest.raises(ValidationError):
        WorldConfig(episode_steps=80)


def test_regression_sensor_offset_positive_time_delta():
    """This is a regression guard: the old sensor-offset sign is already correct."""
    corrector = Corrector()
    values = []
    for step in range(12):
        result = corrector.correct(plan(now=step / 10), 0.08, "position_bias", 1.0)
        values.append(result.time_delta)
    assert values[-1] == pytest.approx(0.08, abs=0.005)


def test_constant_physical_lead_moves_pick_earlier():
    corrector = Corrector()
    result = None
    for step in range(12):
        # 1.008 actual speed produces a growing residual with no sensor offset.
        result = corrector.correct(plan(eta=8.0, now=step / 10), 0.008 * step / 10, "none", 1.0)
    assert result is not None
    assert result.time_delta < 0


def test_nominal_object_near_start_of_range_is_grabbed():
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-7.99,
        initial_position_max=-7.99,
    )
    receipt = run_episode(config, 0, False)
    assert receipt["metrics"]["successes"] == 1


def test_command_uses_applied_plan_arrival_time(monkeypatch):
    import inspect

    from rra.controller import Controller

    seen = []
    original = Controller.execute_2d

    def capture(self, command, actual_x, actual_y, actual_time):
        # execute_2d is called from run_episode while applied_plan is in scope.
        applied_plan = inspect.currentframe().f_back.f_locals["applied_plan"]
        seen.append((command, applied_plan.expected_arrival_time))
        return original(self, command, actual_x, actual_y, actual_time)

    monkeypatch.setattr(Controller, "execute_2d", capture)
    config = WorldConfig(scenario="nominal", object_count=1)
    run_episode(config, 0, False)
    assert seen
    assert all(abs(command.expected_time - arrival_time) < 1e-9 for command, arrival_time in seen)
    assert any(
        abs(command.expected_time / config.dt - round(command.expected_time / config.dt)) > 1e-6
        for command, _ in seen
    )


def test_every_object_has_one_terminal_outcome_and_reason_for_skips():
    receipt = run_episode(WorldConfig(scenario="nominal"), 0, True)
    outcomes = receipt["outcomes"]
    assert len(outcomes) == receipt["config"]["object_count"]
    assert len({row["target_id"] for row in outcomes}) == len(outcomes)
    assert all(row["status"] in {"picked", "attempt_failed", "rejected", "escalated", "skipped"} for row in outcomes)
    assert all(row.get("reason", "").strip() for row in outcomes if row["status"] == "skipped")
    counts = receipt["metrics"]["terminal_counts"]
    assert sum(counts.values()) == receipt["config"]["object_count"]


def test_three_consecutive_failed_or_skipped_outcomes_escalate():
    config = WorldConfig(
        scenario="nominal", object_count=5, episode_steps=90,
        initial_position_min=-8.0, initial_position_max=-8.0,
        tolerance=0.001,
    )
    receipt = run_episode(config, 0, False)
    assert any(row["reason"] == "outcome: consecutive failures" for row in receipt["escalations"])
    assert receipt["safe_stop"] is True
