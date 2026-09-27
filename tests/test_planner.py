import pytest

from rra.planner import ScriptedPlanner
from rra.sim import Observation


def test_planner_uses_nominal_speed_and_observation():
    observation = Observation(
        step=3, time=0.3, target_id=1, observed_x=-1.7, nominal_x=-2.0,
        actual_x=-1.7, nominal_speed=1.0, actual_speed=1.0,
    )
    plan = ScriptedPlanner().plan(observation, 1.0, 0.0)
    assert plan.expected_arrival_time == pytest.approx(2.0)
    assert plan.pick_position == 0.0


def test_planner_rejects_nonpositive_speed():
    observation = Observation(
        step=0, time=0, target_id=1, observed_x=0, nominal_x=0,
        actual_x=0, nominal_speed=1, actual_speed=1,
    )
    with pytest.raises(ValueError):
        ScriptedPlanner().plan(observation, 0, 0)
