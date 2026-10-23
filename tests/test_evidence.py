import json
from hashlib import sha256

import numpy as np

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


def test_runtime_versions_are_receipted_but_excluded_from_receipt_hash():
    receipt = run_episode(WorldConfig(scenario="nominal", object_count=1), 4, True)
    assert receipt["runtime_versions"]["numpy"] == np.__version__
    assert receipt["runtime_versions"]["python"].startswith("3.12.")
    hashed = {key: value for key, value in receipt.items() if key not in (
        "git_sha", "system2_wall_latency_seconds", "system2_verifier_calls",
        "system2_hypotheses_proposed", "system2_calls", "s2_diagnostic_trace",
        "runtime_versions", "receipt_sha256")}
    expected = sha256(json.dumps(hashed, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert receipt["receipt_sha256"] == expected
