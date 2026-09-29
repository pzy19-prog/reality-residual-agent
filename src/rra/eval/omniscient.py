"""Evaluator-side dev-only physical upper-bound analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from time import monotonic
from typing import Any

from rra.eval.framework import v3_world_config
from rra.sim import World

ROOT = Path(__file__).resolve().parents[3]
B2_SCENARIOS = ("drift-high", "moving-mid", "load-mid", "moving-high", "load-high", "combo")


def run_omniscient_upper_bound(seeds: list[int] | None = None) -> dict[str, Any]:
    seed_path = ROOT / "config/dev_seeds.json"
    seeds = seeds if seeds is not None else json.loads(seed_path.read_text())["seeds"]
    cases = json.loads((ROOT / "config/scenarios.json").read_text())["cases"]
    by_name = {case["name"]: case for case in cases}
    started = monotonic()
    rows = []
    for name in B2_SCENARIOS:
        case = by_name[name]
        config = v3_world_config(case["scenario"], **case.get("parameters", {}))
        successes = objects = 0
        max_error = 0.0
        for seed in seeds:
            world = World(config, seed)
            # Oracle chooses the sample with minimum true spatial error and
            # sets expected_time to that true sample time. No policy data enters.
            for _target in range(config.object_count):
                best = float("inf")
                for _step in range(config.episode_steps):
                    observation = world.observation()
                    spatial_error = (
                        (observation.actual_x - config.x_pick) ** 2
                        + (observation.actual_y - config.y_pick) ** 2
                    ) ** 0.5
                    best = min(best, spatial_error)
                    world.advance()
                    if world.step_index == 0:
                        break
                objects += 1
                max_error = max(max_error, best)
                successes += int(best <= config.tolerance)
        rows.append({"scenario": name, "success": round(successes / objects, 6), "successes": successes, "objects": objects})
    return {
        "schema_version": "rra.h1.omniscient-upper-bound.v1",
        "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "subject": "docs/P3_SYSTEM2_DESIGN.md §20.1; §2.1",
        "method": "Evaluator-only oracle scans each true 100-step trajectory, chooses the sample nearest x_pick, and uses its true time as expected_time. Success requires true spatial error <= tolerance; command bounds are unchanged.",
        "seeds": {"path": "config/dev_seeds.json", "values": seeds},
        "scenario_set": list(B2_SCENARIOS),
        "runtime_seconds": round(monotonic() - started, 3),
        "rows": rows,
        "policy_import_or_call": False,
    }
