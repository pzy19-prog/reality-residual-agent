from rra.eval.dev_diagnostics import run_b1_diagnostic
from rra.eval.omniscient import B2_SCENARIOS, run_omniscient_upper_bound


def test_b1_diagnostic_uses_common_v3_framework_and_mode():
    receipt = run_b1_diagnostic("corrected", seeds=[0])
    assert receipt["mode"] == "corrected"
    assert receipt["framework"] == {"dt": 0.1, "episode_steps": 100, "sigma": 0.015}
    assert len(receipt["rows"]) == 14


def test_omniscient_dev_upper_bound_is_exactly_frozen_six_scenarios():
    receipt = run_omniscient_upper_bound(seeds=[0, 1])
    assert receipt["scenario_set"] == list(B2_SCENARIOS)
    assert [row["scenario"] for row in receipt["rows"]] == list(B2_SCENARIOS)
    assert all(row["objects"] == 24 for row in receipt["rows"])
    assert receipt["policy_import_or_call"] is False
