from rra.evidence import run_episode
from rra.sim import WorldConfig


def test_receipt_is_deterministic_excluding_git_sha():
    config = WorldConfig(scenario="bias", object_count=3)
    first = run_episode(config, 3, True, "abc")
    second = run_episode(config, 3, True, "def")
    assert first["receipt_sha256"] == second["receipt_sha256"]
    assert first["git_sha"] != second["git_sha"]
    assert first["compensation_records"] == second["compensation_records"]


def test_unsafe_residual_fails_closed_without_attempts():
    config = WorldConfig(scenario="combo", position_bias=2.0, object_count=2)
    receipt = run_episode(config, 9, True)
    assert receipt["metrics"]["escalations"] > 0
    assert receipt["metrics"]["attempted"] == 0
