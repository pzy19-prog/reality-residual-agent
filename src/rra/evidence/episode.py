"""Episode runner and JSON-compatible evidence receipt."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from rra.controller import Command, Controller, ControllerConfig
from rra.fast import Corrector, ResidualMonitor
from rra.planner import ScriptedPlanner
from rra.sim import World, WorldConfig


def run_episode(
    config: WorldConfig,
    seed: int,
    compensation: bool,
    git_sha: str | None = None,
) -> dict[str, Any]:
    """Run a fixed-step episode and return its complete reproducibility receipt."""
    world = World(config, seed)
    planner = ScriptedPlanner()
    monitor = ResidualMonitor()
    corrector = Corrector()
    controller = Controller(ControllerConfig(tolerance=config.tolerance))
    records: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    errors: list[float] = []
    successes = 0
    attempted_targets: set[int] = set()
    safe_stop = False

    for _ in range(config.episode_steps * config.object_count):
        observation = world.observation()
        residual = monitor.update(observation)
        disturbance = monitor.classify()
        nominal_plan = planner.plan(observation, config.belt_speed, config.x_pick)
        correction = corrector.correct(nominal_plan, residual, disturbance, config.belt_speed)
        if "ESCALATE:" in correction.reason:
            safe_stop = True
            escalations.append({
                "step": observation.step,
                "target_id": observation.target_id,
                "residual": residual,
                "reason": correction.reason,
            })
        applied_plan = correction.plan if compensation else nominal_plan
        if compensation:
            records.append({
                "time": round(observation.time, 6),
                "target_id": observation.target_id,
                "residual": round(residual, 6),
                "classification": disturbance,
                "position_delta": round(correction.position_delta, 6),
                "time_delta": round(correction.time_delta, 6),
                "reason": correction.reason,
            })
        if (not safe_stop and observation.target_id not in attempted_targets
                and abs(observation.time - applied_plan.expected_arrival_time) <= config.dt / 2):
            command = Command(
                target_id=observation.target_id,
                speed=config.belt_speed,
                pick_position=applied_plan.pick_position,
                expected_time=observation.time,
            )
            result = controller.execute(command, observation.actual_x, observation.time)
            attempted_targets.add(observation.target_id)
            errors.append(result.position_error)
            successes += int(result.accepted and result.success)
            if not result.accepted:
                escalations.append({
                    "step": observation.step,
                    "target_id": observation.target_id,
                    "residual": residual,
                    "reason": result.reason,
                })
        world.advance()

    total = max(1, len(attempted_targets))
    receipt: dict[str, Any] = {
        "schema_version": "rra.receipt.v1",
        "config": config.model_dump(mode="json"),
        "seed": int(seed),
        "git_sha": git_sha or "unknown",
        "compensation": "on" if compensation else "off",
        "compensation_records": records,
        "escalations": escalations,
        "metrics": {
            "attempted": len(attempted_targets),
            "successes": successes,
            "success_rate": round(successes / total, 6),
            "mean_abs_error": round(sum(errors) / len(errors), 6) if errors else 0.0,
            "escalations": len(escalations),
        },
    }
    hash_input = {key: value for key, value in receipt.items() if key != "git_sha"}
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt["receipt_sha256"] = sha256(canonical).hexdigest()
    return receipt
