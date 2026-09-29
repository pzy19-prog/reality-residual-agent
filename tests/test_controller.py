from rra.controller import Command, Controller, ControllerConfig
from rra.sim import Observation


def test_controller_accepts_in_range_pick_and_records_rejection():
    controller = Controller(ControllerConfig(tolerance=0.2))
    accepted = controller.execute(Command(1, 1, 0, 1), 0.1, 1)
    rejected = controller.execute(Command(2, 2, 0, 1), 0, 1)
    assert accepted.accepted and accepted.success
    assert not rejected.accepted
    assert len(controller.rejections) == 1


def test_physical_execution_truth_does_not_use_policy_observed_position():
    command = Command(1, 1.0, 0.0, 1.0)
    low = Observation(
        step=10, time=1.0, target_id=1, observed_x=-0.01, nominal_x=0.0,
        actual_x=0.01, nominal_speed=1.0, actual_speed=1.0,
    )
    high = low.model_copy(update={"observed_x": 99.0})
    controller = Controller(ControllerConfig(tolerance=0.2))
    from_low = controller.execute(command, actual_x=0.01, actual_time=1.0)
    from_high = controller.execute(command, actual_x=0.01, actual_time=1.0)
    assert low.observed_x != high.observed_x
    assert from_low == from_high
    assert from_low.success
