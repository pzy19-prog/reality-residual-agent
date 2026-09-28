"""Command line interface for deterministic runs and benchmark suites."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from rra.evidence import run_episode
from rra.sim import WorldConfig

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ("bias", "drift", "moving", "load", "combo")
SCENARIO_CONFIG_PATH = ROOT / "config" / "scenarios.json"
EVAL_SEED_PATH = ROOT / "config" / "eval_seeds.json"


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _load_scenarios() -> list[dict[str, Any]]:
    return json.loads(SCENARIO_CONFIG_PATH.read_text())["cases"]


def _markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| 场景 | 关闭成功率 | 开启成功率 | 开启 coverage | 开启 precision | 关闭 MAE* | 开启 MAE* | 开启终态 picked/failed/rejected/escalated/skipped | 开启升级数 |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['off']['success_rate']:.3f} | "
            f"{row['on']['success_rate']:.3f} | {row['on']['coverage']:.3f} | "
            f"{row['on']['precision']:.3f} | {row['off']['mean_abs_error']:.3f} | "
            f"{row['on']['mean_abs_error']:.3f} | "
            f"{'/'.join(str(row['on']['terminal_counts'][s]) for s in ('picked', 'attempt_failed', 'rejected', 'escalated', 'skipped'))} | "
            f"{row['on']['escalations']} |"
        )
    lines.append("")
    lines.append("* MAE 仅统计已发命令对象；coverage = 发出命令对象数 / 总对象数；precision = picked / 发出命令对象数。")
    return "\n".join(lines)


def _summarize(metrics: list[dict[str, Any]], object_count: int) -> dict[str, Any]:
    successes = sum(item["successes"] for item in metrics)
    attempts = sum(item["attempted"] for item in metrics)
    error_sum = sum(item["absolute_error_sum"] for item in metrics)
    total_objects = len(metrics) * object_count
    return {
        "success_rate": round(successes / total_objects, 6) if total_objects else 0.0,
        "coverage": round(attempts / total_objects, 6) if total_objects else 0.0,
        "precision": round(successes / attempts, 6) if attempts else 0.0,
        "mean_abs_error": round(error_sum / attempts, 6) if attempts else 0.0,
        "attempted": attempts,
        "escalations": sum(item["escalations"] for item in metrics),
        "terminal_counts": {
            state: sum(item.get("terminal_counts", {}).get(state, 0) for item in metrics)
            for state in ("picked", "attempt_failed", "rejected", "escalated", "skipped")
        },
    }


def _run_bench(seeds: list[int], output_dir: Path) -> dict[str, Any]:
    """Run a given seed set; internal helper used for dev validation."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sha = _git_sha()
    rows = []
    cases = _load_scenarios()
    for case in cases:
        scenario = case["scenario"]
        config_values = case.get("parameters", {})
        per_mode: dict[str, list[dict[str, Any]]] = {"on": [], "off": []}
        config = WorldConfig(scenario=scenario, **config_values)
        for seed in seeds:
            for mode in (False, True):
                receipt = run_episode(config, seed, mode, sha)
                per_mode["on" if mode else "off"].append(receipt["metrics"])
        summary = {
            mode: _summarize(metrics, config.object_count)
            for mode, metrics in per_mode.items()
        }
        rows.append({
            "scenario": case["name"],
            "disturbance": scenario,
            "intensity": case.get("intensity"),
            "parameters": config_values,
            "off": summary["off"],
            "on": summary["on"],
            "delta_success_rate": round(summary["on"]["success_rate"] - summary["off"]["success_rate"], 6),
        })
    result = {
        "schema_version": "rra.bench.v2",
        "git_sha": sha,
        "seed_role": "eval" if seeds == json.loads(EVAL_SEED_PATH.read_text())["seeds"] else "dev",
        "seeds": seeds,
        "seed_policy": "Dev seeds 0-129 are for iteration. Eval seeds 1000-1099 are frozen and used only for the final benchmark.",
        "scenario_config": str(SCENARIO_CONFIG_PATH.relative_to(ROOT)),
        "rows": rows,
        "markdown": _markdown(rows),
    }
    (output_dir / "bench.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (output_dir / "bench.md").write_text(result["markdown"] + "\n")
    return result


def run_bench(output_dir: Path = Path(".")) -> dict[str, Any]:
    """Run the frozen eval suite, or a seed file explicitly selected for smoke use."""
    seed_path = Path(os.environ.get("RRA_SEED_FILE", str(EVAL_SEED_PATH)))
    seeds = json.loads(seed_path.read_text())["seeds"]
    return _run_bench(seeds, output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rra")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="run one deterministic episode")
    run_parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    run_parser.add_argument("--seed", type=int, required=True)
    run_parser.add_argument("--compensation", choices=("on", "off"), required=True)
    run_parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    bench_parser = commands.add_parser("bench", help="run the configured benchmark suite")
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
