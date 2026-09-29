import json

import pytest

from rra.evidence import run_episode
from rra.eval.b2_grid import (
    R_VALUES,
    T_VALUES,
    _evaluate_cached,
    _prepare,
    run_b2_grid,
)
from rra.eval.framework import v3_world_config


@pytest.mark.parametrize("scenario", ["drift-high", "moving-high"])
@pytest.mark.parametrize("pair_index", [0, 440])
def test_vector_grid_episode_matches_reference_runner(scenario, pair_index):
    cases = json.loads(open("config/scenarios.json").read())["cases"]
    case = next(row for row in cases if row["name"] == scenario)
    config = v3_world_config(case["scenario"], **case["parameters"])
    t, r = T_VALUES[pair_index // 21], R_VALUES[pair_index % 21]
    cached = _evaluate_cached(_prepare(config, 2), config)
    direct = run_episode(
        config, 2, True, terminal_monitoring="corrected",
        fast_time_limit=t, fast_residual_threshold=r,
    )
    assert cached["successes"][pair_index] == direct["metrics"]["successes"]
    assert cached["attempted"][pair_index] == direct["metrics"]["attempted"]
    assert cached["escalations"][pair_index] == direct["metrics"]["escalations"]
    for state in ("picked", "attempt_failed", "rejected", "escalated", "skipped"):
        assert cached[f"terminal_{state}"][pair_index] == direct["metrics"]["terminal_counts"][state]


def test_grid_is_441_points_over_exact_six_scenarios_and_selects_deterministically():
    first = run_b2_grid(seeds=[0])
    second = run_b2_grid(seeds=[0])
    assert first["grid_points_evaluated"] == 441
    assert first["scenario_set"] == ["drift-high", "moving-mid", "load-mid", "moving-high", "load-high", "combo"]
    assert all(value == 1 for value in first["grid_point_execution_count"].values())
    assert first["selected"] == second["selected"]
