"""Materialization of common-framework B1 dev diagnostic receipts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from time import monotonic
from typing import Any, Literal

from rra.evidence import run_episode
from rra.eval.framework import v3_world_config

ROOT = Path(__file__).resolve().parents[3]


def _head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def run_b1_diagnostic(mode: Literal["legacy", "corrected"], seeds: list[int] | None = None) -> dict[str, Any]:
    seed_path = ROOT / "config/dev_seeds.json"
    seeds = seeds if seeds is not None else json.loads(seed_path.read_text())["seeds"]
    cases = json.loads((ROOT / "config/scenarios.json").read_text())["cases"]
    started = monotonic()
    subject_sha = _head()
    rows: list[dict[str, Any]] = []
    for case in cases:
        config = v3_world_config(case["scenario"], **case.get("parameters", {}))
        totals = {"successes": 0, "attempted": 0, "absolute_error_sum": 0.0, "escalations": 0}
        terminals = {s: 0 for s in ("picked", "attempt_failed", "rejected", "escalated", "skipped")}
        for seed in seeds:
            m = run_episode(config, seed, True, git_sha=subject_sha, terminal_monitoring=mode)["metrics"]
            for key in totals:
                totals[key] += m[key]
            for state in terminals:
                terminals[state] += m["terminal_counts"][state]
        n = len(seeds) * config.object_count
        rows.append({
            "scenario": case["name"],
            "success": round(totals["successes"] / n, 6),
            "coverage": round(totals["attempted"] / n, 6),
            "precision": round(totals["successes"] / totals["attempted"], 6) if totals["attempted"] else 0.0,
            "mae": round(totals["absolute_error_sum"] / totals["attempted"], 6) if totals["attempted"] else 0.0,
            "terminal_counts": terminals,
            "escalations": totals["escalations"],
        })
    return {
        "schema_version": "rra.h1.b1-dev-diagnostic.v1",
        "git_sha": subject_sha,
        "mode": mode,
        "framework": {"dt": 0.1, "episode_steps": 100, "sigma": 0.015},
        "seeds": {"path": "config/dev_seeds.json", "values": seeds},
        "workers": 1,
        "runtime_seconds": round(monotonic() - started, 3),
        "rows": rows,
    }
