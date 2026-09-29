"""F1 legacy behavior-equivalence anchor for the sanitized B1 path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rra.evidence import run_episode
from rra.sim import WorldConfig

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    "nominal": (1.000, 1.000, 1.000, 0.051, (1560, 0, 0, 0, 0), 0),
    "bias-low": (1.000, 1.000, 1.000, 0.051, (1560, 0, 0, 0, 0), 0),
    "bias-mid": (1.000, 1.000, 1.000, 0.051, (1560, 0, 0, 0, 0), 0),
    "bias-high": (1.000, 1.000, 1.000, 0.051, (1560, 0, 0, 0, 0), 0),
    "drift-low": (1.000, 1.000, 1.000, 0.051, (1560, 0, 0, 0, 0), 0),
    "drift-mid": (1.000, 1.000, 1.000, 0.052, (1560, 0, 0, 0, 0), 0),
    "drift-high": (0.987, 1.000, 0.987, 0.079, (1539, 21, 0, 0, 0), 0),
    "moving-low": (1.000, 1.000, 1.000, 0.052, (1560, 0, 0, 0, 0), 0),
    "moving-mid": (0.818, 0.863, 0.947, 0.088, (1276, 71, 0, 0, 213), 5),
    "moving-high": (0.008, 0.011, 0.765, 0.179, (13, 4, 0, 1442, 101), 130),
    "load-low": (1.000, 1.000, 1.000, 0.052, (1560, 0, 0, 0, 0), 0),
    "load-mid": (0.651, 0.676, 0.964, 0.080, (1016, 38, 0, 0, 506), 21),
    "load-high": (0.022, 0.025, 0.897, 0.099, (35, 4, 0, 1456, 65), 130),
    "combo": (0.008, 0.009, 0.929, 0.149, (13, 1, 0, 1546, 0), 130),
}


def build_legacy_anchor() -> dict[str, Any]:
    """Run the exact REPAIR-04 anchor and return precision-normalized rows."""
    seeds = json.loads((ROOT / "config/dev_seeds.json").read_text())["seeds"]
    scenarios = json.loads((ROOT / "config/scenarios.json").read_text())["cases"]
    rows: list[dict[str, Any]] = []
    for case in scenarios:
        config = WorldConfig(scenario=case["scenario"], **case.get("parameters", {}))
        successes = attempts = escalation_count = 0
        errors = 0.0
        terminals = {key: 0 for key in ("picked", "attempt_failed", "rejected", "escalated", "skipped")}
        for seed in seeds:
            metrics = run_episode(config, seed, True)["metrics"]
            successes += metrics["successes"]
            attempts += metrics["attempted"]
            escalation_count += metrics["escalations"]
            errors += metrics["absolute_error_sum"]
            for state in terminals:
                terminals[state] += metrics["terminal_counts"][state]
        total = len(seeds) * config.object_count
        row = {
            "scenario": case["name"],
            "success": round(successes / total, 3),
            "coverage": round(attempts / total, 3),
            "precision": round(successes / attempts, 3) if attempts else 0.0,
            "mae": round(errors / attempts, 3) if attempts else 0.0,
            "terminal_counts": [terminals[key] for key in terminals],
            "escalations": escalation_count,
        }
        rows.append(row)
    return {
        "schema_version": "rra.h1.legacy-equivalence.v1",
        "subject": "diag/REPAIR-04.md",
        "seeds": {"path": "config/dev_seeds.json", "count": len(seeds), "first": seeds[0], "last": seeds[-1]},
        "config": {"sigma": 0, "episode_steps": 90, "post_terminal_monitoring": "legacy-on", "compensation": "on"},
        "rows": rows,
    }


def assert_legacy_anchor(receipt: dict[str, Any]) -> None:
    rows = receipt["rows"]
    if [row["scenario"] for row in rows] != list(EXPECTED):
        raise AssertionError("legacy anchor scenario order differs")
    for row in rows:
        expected = EXPECTED[row["scenario"]]
        actual = (row["success"], row["coverage"], row["precision"], row["mae"], tuple(row["terminal_counts"]), row["escalations"])
        if actual != expected:
            raise AssertionError(f"legacy anchor mismatch for {row['scenario']}: expected {expected}, got {actual}")
