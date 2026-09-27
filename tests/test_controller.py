from rra.controller import Command, Controller, ControllerConfig


def test_controller_accepts_in_range_pick_and_records_rejection():
    controller = Controller(ControllerConfig(tolerance=0.2))
    accepted = controller.execute(Command(1, 1, 0, 1), 0.1, 1)
    rejected = controller.execute(Command(2, 2, 0, 1), 0, 1)
    assert accepted.accepted and accepted.success
    assert not rejected.accepted
    assert len(controller.rejections) == 1
