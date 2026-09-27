"""Command line interface for runs and fixed eval-seed benchmarks."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from statistics import fmean
from typing import Any

from rra.evidence import run_episode
from rra.sim import WorldConfig

SCENARIOS = ("bias", "drift", "moving", "load", "combo")
EVAL_SEEDS = tuple(range(100, 130))


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| 场景 | 补偿关闭成功率 | 补偿开启成功率 | 差值 | 关闭 MAE | 开启 MAE | 开启升级数 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['off']['success_rate']:.3f} | "
            f"{row['on']['success_rate']:.3f} | {row['delta_success_rate']:+.3f} | "
            f"{row['off']['mean_abs_error']:.3f} | {row['on']['mean_abs_error']:.3f} | "
            f"{row['on']['escalations']} |"
        )
    return "\n".join(lines)


def run_bench(output_dir: Path = Path(".")) -> dict[str, Any]:
    """Evaluate all scenarios on the fixed, disjoint eval-seed set 100..129."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sha = _git_sha()
    rows = []
    for scenario in SCENARIOS:
        per_mode: dict[str, list[dict[str, Any]]] = {"on": [], "off": []}
        for seed in EVAL_SEEDS:
            config = WorldConfig(scenario=scenario)
            for mode in (False, True):
                receipt = run_episode(config, seed, mode, sha)
                per_mode["on" if mode else "off"].append(receipt["metrics"])
        summary = {}
        for mode, metrics in per_mode.items():
            attempted = sum(item["attempted"] for item in metrics)
            successes = sum(item["successes"] for item in metrics)
            summary[mode] = {
                "success_rate": round(successes / (len(metrics) * config.object_count), 6) if metrics else 0.0,
                "mean_abs_error": round(fmean(item["mean_abs_error"] for item in metrics), 6),
                "escalations": sum(item["escalations"] for item in metrics),
            }
        rows.append({
            "scenario": scenario,
            "off": summary["off"],
            "on": summary["on"],
            "delta_success_rate": round(summary["on"]["success_rate"] - summary["off"]["success_rate"], 6),
        })
    result = {
        "schema_version": "rra.bench.v1",
        "git_sha": sha,
        "tune_seeds": list(range(0, 10)),
        "eval_seeds": list(EVAL_SEEDS),
        "seed_policy": "Tune seeds 0-9 are disjoint from fixed evaluation seeds 100-129.",
        "rows": rows,
        "markdown": _markdown(rows),
    }
    (output_dir / "bench.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (output_dir / "bench.md").write_text(result["markdown"] + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rra")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="run one deterministic episode")
    run_parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    run_parser.add_argument("--seed", type=int, required=True)
    run_parser.add_argument("--compensation", choices=("on", "off"), required=True)
    run_parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    bench_parser = commands.add_parser("bench", help="run the fixed 5x2 eval benchmark")
    bench_parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    if args.command == "run":
        args.output_dir.mkdir(parents=True, exist_ok=True)
        receipt = run_episode(
            WorldConfig(scenario=args.scenario),
            args.seed,
            args.compensation == "on",
            _git_sha(),
        )
        path = args.output_dir / f"{args.scenario}-seed{args.seed}-{args.compensation}.json"
        path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
        print(path)
        return 0
    result = run_bench(args.output_dir)
    print(result["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
