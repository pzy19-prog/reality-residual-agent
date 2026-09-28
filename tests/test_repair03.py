"""RRA-03 behavior tests. Tests prefixed regression are compatibility guards."""

from rra.evidence import run_episode
from rra.fast import Corrector
from rra.fast.residual import MAX_TIME_CORRECTION
from rra.planner import Plan
from rra.sim import World, WorldConfig


def _plan(eta: float, now: float = 0.0) -> Plan:
    return Plan(target_id=0, expected_arrival_time=eta, pick_position=0.0, observation_time=now)


def test_saturated_moving_correction_skips_without_command():
    config = WorldConfig(
        scenario="moving", object_count=1, initial_position_min=-8.0,
        initial_position_max=-8.0, episode_steps=100,
    )
    receipt = run_episode(config, 0, True, include_trace=True)

    assert receipt["outcomes"][0]["status"] == "skipped"
    assert receipt["outcomes"][0]["reason"] == "correction_saturated"
    assert receipt["metrics"]["attempted"] == 0
    assert not receipt["failure_trace"][0]["command_issued"]


def test_moving_lead_uses_actual_speed_for_eta_conversion():
    corrector = Corrector()
    corrector.correct(_plan(3.0), 0.0, "moving_target", 1.0)
    correction = corrector.correct(_plan(3.0, 0.1), 0.01, "moving_target", 1.0)

    # A +0.10 speed delta over a 3 s nominal ETA advances arrival by 3 - 3/1.1.
    true_eta_delta = 3.0 / 1.1 - 3.0
    assert abs(correction.time_delta - true_eta_delta) < 0.01 / 2


def test_default_time_correction_limit_uses_shared_constant():
    """Regression guard: default correction bound stays linked to horizon policy."""
    assert Corrector().max_time_correction == MAX_TIME_CORRECTION == 0.50


def test_world_horizon_uses_shared_time_correction_limit(monkeypatch):
    """Regression guard: changing the shared bound changes the validated horizon."""
    import pytest
    import rra.sim.world as world_module

    monkeypatch.setattr(world_module, "MAX_TIME_CORRECTION", MAX_TIME_CORRECTION + 0.01)
    with pytest.raises(ValueError, match="do not cover"):
        WorldConfig(
            scenario="nominal", initial_position_min=-8.0,
            initial_position_max=-8.0, episode_steps=87,
        )


def test_window_crossed_between_samples_still_issues_one_command(monkeypatch):
    calls = []
    original_advance = World.advance
    original_execute = __import__("rra.controller", fromlist=["Controller"]).Controller.execute_2d

    def skip_one_sample(self):
        original_advance(self)
        if self.step_index < self.config.episode_steps:
            original_advance(self)
        if self.step_index < self.config.episode_steps:
            original_advance(self)

    def capture(self, command, actual_x, actual_y, actual_time):
        calls.append(command.target_id)
        return original_execute(self, command, actual_x, actual_y, actual_time)

    monkeypatch.setattr(World, "advance", skip_one_sample)
    from rra.controller import Controller

    monkeypatch.setattr(Controller, "execute_2d", capture)
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-0.15,
        initial_position_max=-0.15, episode_steps=90,
    )
    receipt = run_episode(config, 0, False)

    assert len(calls) == 1
    assert calls == [0]
    assert receipt["metrics"]["attempted"] == 1
