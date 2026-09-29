"""Mechanical C4 structural holdout and C5 seed prohibition checks."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

from rra.eval.scenarios import PRIMITIVES

P3_SHA = "024ea2e3e66b91f5a2157a66c073493e7107e109"
EXCLUDED = ("SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP")


def structural_holdout() -> dict[str, Any]:
    """Compute the registered nine-way ordered structural holdout."""
    import itertools

    pre_exclusion = [
        {"id": f"AND({','.join(items)})", "primitives": list(items)}
        for size in (2, 3)
        for items in itertools.combinations(PRIMITIVES, size)
    ]
    excluded_id = f"AND({','.join(EXCLUDED)})"
    eligible = [row for row in pre_exclusion if row["id"] != excluded_id]
    index = int(P3_SHA, 16) % len(eligible)
    return {
        "canonical_primitive_order": list(PRIMITIVES),
        "pre_exclusion_candidates": pre_exclusion,
        "excluded_frozen_v0_combo": excluded_id,
        "eligible_ordered_candidates": eligible,
        "p3_sha": P3_SHA,
        "modulus": len(eligible),
        "holdout_index": index,
        "holdout_id": eligible[index]["id"],
    }


def final_eval_v3_prohibition(root: Path) -> dict[str, Any]:
    """Record absence without opening or materializing any final seed values."""
    forbidden = root / "config/eval_seeds_v3.json"
    tracked = subprocess_git_files(root)
    equivalent = [
        path for path in tracked
        if "eval_seeds_v3" in Path(path).name.lower()
        or "final_eval_v3" in Path(path).name.lower()
    ]
    return {
        "schema_version": "rra.h1.final-eval-v3-prohibition.v1",
        "checked_path_existence_only": "config/eval_seeds_v3.json",
        "forbidden_seed_file_exists": forbidden.exists(),
        "tracked_equivalent_seed_paths": equivalent,
        "final_eval_v3_seed_values_created": False,
        "final_eval_v3_seed_values_inspected": False,
        "generation_stage": "H5 only, after implementation-candidate freeze, isolated process/context, P3 §18.1",
    }


def subprocess_git_files(root: Path) -> list[str]:
    output = subprocess.run(["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True).stdout
    return output.splitlines()


def add_receipt_hash(receipt: dict[str, Any]) -> dict[str, Any]:
    value = dict(receipt)
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value["receipt_sha256"] = sha256(canonical).hexdigest()
    return value


def materialize_holdout_receipts(root: Path) -> tuple[Path, Path]:
    """Write the two small H1-09 receipts without reading any final seed values."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    base = root / "artifacts/h1"
    base.mkdir(parents=True, exist_ok=True)
    holdout = add_receipt_hash({
        "schema_version": "rra.h1.structural-holdout.v1",
        "source_commit": head,
        **structural_holdout(),
    })
    prohibition = add_receipt_hash({
        "source_commit": head,
        **final_eval_v3_prohibition(root),
    })
    holdout_path = base / "structural-holdout.json"
    prohibition_path = base / "final-eval-v3-prohibition.json"
    holdout_path.write_text(json.dumps(holdout, indent=2) + "\n")
    prohibition_path.write_text(json.dumps(prohibition, indent=2) + "\n")
    return holdout_path, prohibition_path
