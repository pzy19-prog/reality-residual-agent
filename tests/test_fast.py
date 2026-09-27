from rra.fast import Corrector, ResidualMonitor
from rra.planner import Plan
from rra.sim import Observation


def observation(step: int, residual: float) -> Observation:
    return Observation(
        step=step, time=step / 10, target_id=0, observed_x=residual,
        nominal_x=0, actual_x=0, nominal_speed=1, actual_speed=1,
    )


def test_monitor_reports_residual_window_and_bias_classification():
    monitor = ResidualMonitor(window_size=5)
    for step in range(5):
        monitor.update(observation(step, 0.3))
    assert monitor.mean == 0.3
    assert monitor.max_abs == 0.3
    assert monitor.classify() == "position_bias"


def test_monitor_recognizes_step_change():
    monitor = ResidualMonitor(window_size=6)
    for step, residual in enumerate((0, 0, 0, 0.2, 0.2, 0.2)):
        monitor.update(observation(step, residual))
    assert monitor.classify() == "load_change"


def test_corrector_clamps_and_escalates_without_relaxing_threshold():
    corrector = Corrector(max_time_correction=0.1, safe_residual_threshold=0.7)
    plan = Plan(target_id=0, expected_arrival_time=1, pick_position=0)
    result = corrector.correct(plan, 0.5, "position_bias", 1)
    assert abs(result.time_delta) <= 0.1
    unsafe = corrector.correct(plan, 0.71, "unknown", 1)
    assert unsafe.reason.startswith("ESCALATE:")
    assert unsafe.plan == plan
