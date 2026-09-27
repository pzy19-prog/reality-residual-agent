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
    base_plans: dict[int, Any] = {}
    active_target: int | None = None
    controller = Controller(ControllerConfig(tolerance=config.tolerance))
    records: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    errors: list[float] = []
    successes = 0
    attempted_targets: set[int] = set()
    safe_stop = False

    for _ in range(config.episode_steps * config.object_count):
        observation = world.observation()
        if active_target != observation.target_id:
            active_target = observation.target_id
            monitor = ResidualMonitor()
            corrector = Corrector()
        residual = monitor.update(observation)
        disturbance = monitor.classify()
        if observation.target_id not in base_plans:
            base_plans[observation.target_id] = planner.plan(observation, config.belt_speed, config.x_pick)
        base_plan = base_plans[observation.target_id]
        working_plan = base_plan.model_copy(update={"observation_time": observation.time})
        correction = corrector.correct(working_plan, residual, disturbance, config.belt_speed)
        nominal_plan = working_plan
        if "ESCALATE:" in correction.reason:
            if not safe_stop:
                escalations.append({
                    "step": observation.step,
                    "target_id": observation.target_id,
                    "residual": residual,
                    "reason": correction.reason,
                })
            safe_stop = True
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
                pick_y=config.y_pick,
            )
            response_delay = (
                config.load_response_delay
                if config.scenario in ("load", "combo") and observation.step >= config.load_step
                else 0.0
            )
            delayed_x = observation.actual_x + observation.actual_speed * response_delay
            result = controller.execute_2d(
                command,
                delayed_x,
                observation.actual_y,
                observation.time + response_delay,
            )
            attempted_targets.add(observation.target_id)
            errors.append(result.position_error)
            successes += int(result.accepted and result.success)
            if not result.accepted:
                safe_stop = True
                escalations.append({
                    "step": observation.step,
                    "target_id": observation.target_id,
                    "residual": residual,
                    "reason": result.reason,
                })
        world.advance()

    total = max(1, config.object_count)
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
