"""Canonical 441-point B2 calibration using shared episode signal caches."""

from __future__ import annotations

import json
from hashlib import sha256
import subprocess
from math import isclose, sqrt
from pathlib import Path
from time import monotonic
from typing import Any

import numpy as np

from rra.evidence.policy import sanitize_observation
from rra.fast import Corrector, ResidualMonitor
from rra.planner import ScriptedPlanner
from rra.sim import World
from rra.eval.framework import v3_world_config
from rra.eval.omniscient import B2_SCENARIOS

ROOT = Path(__file__).resolve().parents[3]
T_VALUES = tuple(round(0.50 + 0.05 * i, 2) for i in range(21))
R_VALUES = tuple(round(1.25 + 0.10 * i, 2) for i in range(21))


def _prepare(config, seed: int) -> list[list[dict[str, float | bool]]]:
    """Precompute threshold-independent policy signals and true plant samples."""
    world = World(config, seed)
    targets: list[list[dict[str, float | bool]]] = []
    planner = ScriptedPlanner()
    for target_id in range(config.object_count):
        monitor = ResidualMonitor()
        corrector = Corrector(
            tolerance=config.tolerance,
            max_time_correction=1.50,
            safe_residual_threshold=1e9,
        )
        base_plan = None
        samples = []
        for _ in range(config.episode_steps):
            raw = world.observation()
            obs = sanitize_observation(raw)
            if base_plan is None:
                base_plan = planner.plan(obs, config.belt_speed, config.x_pick)
            residual = monitor.update(obs)
            disturbance = monitor.classify()
            plan = base_plan.model_copy(update={"observation_time": obs.time})
            correction = corrector.correct(plan, residual, disturbance, config.belt_speed)
            samples.append({
                "time": obs.time,
                "residual": residual,
                "eta": base_plan.expected_arrival_time,
                "raw_delta": correction.uncapped_time_delta,
                "v_hat": correction.v_hat,
                "force_escalate": "ESCALATE:" in correction.reason,
                "actual_x": raw.actual_x,
                "actual_y": raw.actual_y,
                "actual_time": raw.time,
            })
            world.advance()
        targets.append(samples)
    return targets


def _evaluate_cached(targets, config, pairs: int = 441) -> dict[str, np.ndarray]:
    """Evaluate all parameter pairs together over one physical episode."""
    t = np.repeat(np.asarray(T_VALUES, dtype=np.float64), len(R_VALUES))[:pairs]
    r = np.tile(np.asarray(R_VALUES, dtype=np.float64), len(T_VALUES))[:pairs]
    successes = np.zeros(pairs, dtype=np.int64)
    attempted = np.zeros(pairs, dtype=np.int64)
    escalations = np.zeros(pairs, dtype=np.int64)
    terminal = {s: np.zeros(pairs, dtype=np.int64) for s in ("picked", "attempt_failed", "rejected", "escalated", "skipped")}
    safe_stop = np.zeros(pairs, dtype=bool)
    consecutive_failures = np.zeros(pairs, dtype=np.int64)
    outcome_escalation_recorded = np.zeros(pairs, dtype=bool)
    correction_escalation_recorded = np.zeros(pairs, dtype=bool)

    for samples in targets:
        ended = np.zeros(pairs, dtype=bool)
        for sample in samples:
            # Safe stop inhibits commands but diagnostics continue for later
            # objects, matching the frozen runner's episode-level semantics.
            active = ~ended
            if not np.any(active):
                continue
            force = bool(sample["force_escalate"])
            escalate = active & (force | (abs(float(sample["residual"])) > r))
            if np.any(escalate):
                terminal["escalated"][escalate] += 1
                first_escalation = escalate & ~safe_stop & ~correction_escalation_recorded
                escalations[first_escalation] += 1
                correction_escalation_recorded[escalate] = True
                ended[escalate] = True
                safe_stop[escalate] = True
                consecutive_failures[escalate] = 0
            active &= ~escalate
            if not np.any(active):
                continue
            raw_delta = float(sample["raw_delta"])
            clipped = np.clip(raw_delta, -t, t)
            eta = float(sample["eta"]) + clipped
            reached = float(sample["time"]) >= eta - config.dt / 2
            excess = abs(raw_delta - clipped)
            infeasible = excess * float(sample["v_hat"]) > config.tolerance
            skipped = active & ~safe_stop & infeasible & reached
            if np.any(skipped):
                terminal["skipped"][skipped] += 1
                ended[skipped] = True
                consecutive_failures[skipped] += 1
                triggered = skipped & (consecutive_failures >= 3) & ~outcome_escalation_recorded
                if np.any(triggered):
                    escalations[triggered] += 1
                    safe_stop[triggered] = True
                    outcome_escalation_recorded[triggered] = True
            active &= ~skipped
            command = active & ~safe_stop & reached
            if not np.any(command):
                continue
            attempted[command] += 1
            position_error = np.sqrt(
                (float(sample["actual_x"]) - config.x_pick) ** 2
                + (float(sample["actual_y"]) - config.y_pick) ** 2
            )
            time_error = abs(float(sample["actual_time"]) - eta) * config.belt_speed
            error = np.maximum(position_error, time_error)
            picked = command & (error <= config.tolerance)
            failed = command & ~picked
            successes[picked] += 1
            terminal["picked"][picked] += 1
            terminal["attempt_failed"][failed] += 1
            ended[command] = True
            consecutive_failures[picked] = 0
            consecutive_failures[failed] += 1
            triggered = failed & (consecutive_failures >= 3) & ~outcome_escalation_recorded
            if np.any(triggered):
                escalations[triggered] += 1
                safe_stop[triggered] = True
                outcome_escalation_recorded[triggered] = True
        missed = ~ended
        if np.any(missed):
            terminal["skipped"][missed] += 1
            consecutive_failures[missed] += 1
            triggered = missed & (consecutive_failures >= 3) & ~outcome_escalation_recorded
            if np.any(triggered):
                escalations[triggered] += 1
                safe_stop[triggered] = True
                outcome_escalation_recorded[triggered] = True
    return {"successes": successes, "attempted": attempted, "escalations": escalations, **{f"terminal_{k}": v for k, v in terminal.items()}}


def run_b2_grid(seeds: list[int] | None = None) -> dict[str, Any]:
    """Run every frozen grid point exactly once; canonical output by (T,R)."""
    seed_path = ROOT / "config/dev_seeds.json"
    seeds = seeds if seeds is not None else json.loads(seed_path.read_text())["seeds"]
    cases = json.loads((ROOT / "config/scenarios.json").read_text())["cases"]
    by_name = {case["name"]: case for case in cases}
    started = monotonic()
    grid: dict[tuple[float, float], dict[str, Any]] = {
        (t, r): {"T": t, "R": r, "scenarios": {}} for t in T_VALUES for r in R_VALUES
    }
    for name in B2_SCENARIOS:
        case = by_name[name]
        config = v3_world_config(case["scenario"], **case.get("parameters", {}))
        success_totals = np.zeros(441, dtype=np.int64)
        for seed in seeds:
            result = _evaluate_cached(_prepare(config, seed), config)
            success_totals += result["successes"]
        rates = success_totals / (len(seeds) * config.object_count)
        ordered_pairs = [(t, r) for t in T_VALUES for r in R_VALUES]
        for index, (t, r) in enumerate(ordered_pairs):
            grid[(t, r)]["scenarios"][name] = round(float(rates[index]), 6)

    upper_path = ROOT / "artifacts/h1/omniscient-upper-bound.json"
    upper = json.loads(upper_path.read_text())
    u_s = {row["scenario"]: row["success"] for row in upper["rows"]}
    pairs = list(grid.values())
    for row in pairs:
        row["eligible"] = all(row["scenarios"][name] >= u_s[name] - 0.02 for name in B2_SCENARIOS)
        row["cost"] = sqrt(((row["T"] - 0.50) / 1.00) ** 2 + ((row["R"] - 1.25) / 2.00) ** 2)
    eligible = [row for row in pairs if row["eligible"]]
    if eligible:
        min_cost = min(row["cost"] for row in eligible)
        tied = [row for row in eligible if isclose(row["cost"], min_cost, rel_tol=0.0, abs_tol=1e-12)]
        selected = min(tied, key=lambda row: (row["T"], row["R"]))
        reason = "minimum-cost eligible pair"
    else:
        ratios = {id(row): min(row["scenarios"][name] / u_s[name] for name in B2_SCENARIOS) for row in pairs}
        best_ratio = max(ratios.values())
        tied_ratio = [row for row in pairs if isclose(ratios[id(row)], best_ratio, rel_tol=0.0, abs_tol=1e-12)]
        min_cost = min(row["cost"] for row in tied_ratio)
        tied_cost = [row for row in tied_ratio if isclose(row["cost"], min_cost, rel_tol=0.0, abs_tol=1e-12)]
        selected = min(tied_cost, key=lambda row: (row["T"], row["R"]))
        reason = "fallback maximum minimum success/U_s ratio"
    receipt = {
        "schema_version": "rra.h1.b2-grid.v1",
        "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "seed_identity": {"path": "config/dev_seeds.json", "values": seeds},
        "scenario_set": list(B2_SCENARIOS),
        "U_s": u_s,
        "T_values": list(T_VALUES),
        "R_values": list(R_VALUES),
        "grid_points_evaluated": len(pairs),
        "grid_point_execution_count": {f"{row['T']:.2f},{row['R']:.2f}": 1 for row in pairs},
        "runtime_seconds": round(monotonic() - started, 3),
        "workers": 1,
        "selection_reason": reason,
        "selected": selected,
        "rows": pairs,
    }
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt["receipt_sha256"] = sha256(canonical).hexdigest()
    return receipt
