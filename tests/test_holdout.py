import json
from pathlib import Path
import subprocess

from rra.eval.holdout import final_eval_v3_prohibition, structural_holdout


def test_mechanical_holdout_is_preregistered_index_five():
    receipt = structural_holdout()
    assert receipt["holdout_index"] == 5
    assert receipt["holdout_id"] == "AND(SPEED_STEP,ACTUATOR_DELAY)"
    assert len(receipt["pre_exclusion_candidates"]) == 10
    assert len(receipt["eligible_ordered_candidates"]) == 9


def assert_final_seed_rule(root: Path) -> None:
    seed_file = root / "config/eval_seeds_v3.json"
    if not seed_file.exists():
        receipt = final_eval_v3_prohibition(root)
        assert receipt["forbidden_seed_file_exists"] is False
        assert receipt["tracked_equivalent_seed_paths"] == []
        assert receipt["final_eval_v3_seed_values_created"] is False
        assert receipt["final_eval_v3_seed_values_inspected"] is False
        return

    additions = subprocess.run(
        ["git", "log", "--all", "--diff-filter=A", "--format=%H", "--",
         "config/eval_seeds_v3.json"], cwd=root, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert additions
    introduced_in = additions[-1]
    changed_paths = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", introduced_in],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert changed_paths == ["config/eval_seeds_v3.json"]
    committed = subprocess.run(
        ["git", "show", f"{introduced_in}:config/eval_seeds_v3.json"],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(committed)
    seeds = data["seeds"]
    assert data["schema_version"] == "rra.eval-seeds.v3"
    assert data["role"] == "eval_v3"
    assert data["count"] == 100 and len(seeds) == 100
    assert data["range"] == [10000, 2147483647]
    assert len(seeds) == len(set(seeds))
    assert all(type(seed) is int and 10000 <= seed < 2147483647 for seed in seeds)


def test_final_eval_v3_seed_realization_is_absent():
    assert_final_seed_rule(Path.cwd())
