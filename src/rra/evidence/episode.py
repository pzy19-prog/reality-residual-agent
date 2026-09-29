"""Episode runner and JSON-compatible evidence receipt."""

from __future__ import annotations

from hashlib import sha256
import json
from dataclasses import asdict, replace
from typing import Any, Literal

from rra.controller import Command, Controller, ControllerConfig
from rra.fast import Corrector, ResidualMonitor
from rra.planner import ScriptedPlanner
from rra.evidence.policy import command_feedback, sanitize_config, sanitize_observation
from rra.sim import World, WorldConfig
from rra.eval.scenarios import EpisodeRealization
from rra.sim.v3_world import V3World

TERMINAL_STATES = ("picked", "attempt_failed", "rejected", "escalated", "skipped")
CONSECUTIVE_OUTCOME_FAILURE_THRESHOLD = 3


def run_episode(
    config: WorldConfig,
    seed: int,
    compensation: bool,
    git_sha: str | None = None,
    include_trace: bool = False,
    terminal_monitoring: Literal["legacy", "corrected"] = "legacy",
    realization: EpisodeRealization | None = None,
    text_context: str = "",
    fast_time_limit: float = 0.50,
    fast_residual_threshold: float = 1.25,
) -> dict[str, Any]:
    """Run a fixed-step episode and return its complete reproducibility receipt."""
    world = V3World(config, seed, realization) if realization is not None else World(config, seed)
    known_config = sanitize_config(config)
    planner = ScriptedPlanner()
    monitor = ResidualMonitor()
    corrector = Corrector(
        tolerance=known_config.tolerance,
        max_time_correction=fast_time_limit,
        safe_residual_threshold=fast_residual_threshold,
    )
    base_plans: dict[int, Any] = {}
    active_target: int | None = None
    controller = Controller(ControllerConfig(tolerance=config.tolerance))
    records: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    errors: list[float] = []
    successes = 0
    attempted_targets: set[int] = set()
    safe_stop = False
    consecutive_outcome_failures = 0
    outcomes_by_target: dict[int, dict[str, Any]] = {}
    evaluator_objects: dict[int, dict[str, Any]] = {}
    trace_by_target: dict[int, dict[str, Any]] = {}
    object_grab_end_times: dict[int, float] = {}
    policy_feedbacks: list[dict[str, Any]] = []

    def record_outcome(
        target_id: int,
        status: str,
        reason: str,
        step: int,
        residual: float,
    ) -> None:
        nonlocal consecutive_outcome_failures, safe_stop
        if target_id in outcomes_by_target:
            return
        outcomes_by_target[target_id] = {
            "target_id": target_id,
            "status": status,
            "reason": reason,
        }
        evaluator_objects.setdefault(target_id, {"target_id": target_id})["terminal_status"] = status
        if status in ("attempt_failed", "skipped"):
            consecutive_outcome_failures += 1
            if consecutive_outcome_failures >= CONSECUTIVE_OUTCOME_FAILURE_THRESHOLD:
                escalation_reason = "outcome: consecutive failures"
                if not any(row["reason"] == escalation_reason for row in escalations):
                    escalations.append({
                        "step": step,
                        "target_id": target_id,
                        "residual": residual,
                        "reason": escalation_reason,
                    })
                safe_stop = True
        else:
            consecutive_outcome_failures = 0

    for _ in range(config.episode_steps * config.object_count):
        plant_observation = world.observation()
        evaluator_row = evaluator_objects.setdefault(plant_observation.target_id, {
            "target_id": plant_observation.target_id,
            "target_exists_at_execution": None,
            "command_issued": False,
            "execution_step": None,
            "position_error": None,
            "stale_authorization": False,
        })
        if not plant_observation.target_present:
            # A dropped object yields no policy observation. Its existence flag
            # remains evaluator-side and the raw sample never reaches sanitizer.
            world.advance()
            continue
        observation = sanitize_observation(plant_observation)
        if active_target != observation.target_id:
            if active_target is not None and active_target not in outcomes_by_target:
                record_outcome(
                    active_target,
                    "skipped",
                    "safe_stop_before_command" if safe_stop else "prediction_window_missed_before_command",
                    config.episode_steps - 1,
                    0.0,
                )
            active_target = observation.target_id
            monitor = ResidualMonitor()
            corrector = Corrector(
                tolerance=known_config.tolerance,
                max_time_correction=fast_time_limit,
                safe_residual_threshold=fast_residual_threshold,
            )
        if terminal_monitoring == "corrected" and observation.target_id in outcomes_by_target:
            # Terminal objects are inert for all policy diagnostics and updates.
            world.advance()
            continue
        residual = monitor.update(observation)
        disturbance = monitor.classify()
        if observation.target_id not in base_plans:
            base_plans[observation.target_id] = planner.plan(
                observation, known_config.belt_speed, known_config.x_pick
            )
        base_plan = base_plans[observation.target_id]
        working_plan = base_plan.model_copy(update={"observation_time": observation.time})
        correction = corrector.correct(working_plan, residual, disturbance, known_config.belt_speed)
        nominal_plan = working_plan
        if "ESCALATE:" in correction.reason:
            record_outcome(
                observation.target_id,
                "escalated",
                correction.reason,
                observation.step,
                residual,
            )
            if not safe_stop:
                escalations.append({
                    "step": observation.step,
                    "target_id": observation.target_id,
                    "residual": residual,
                    "reason": correction.reason,
                })
            safe_stop = True
        applied_plan = correction.plan if compensation else nominal_plan
        if include_trace:
            trace = trace_by_target.setdefault(observation.target_id, {
                "target_id": observation.target_id,
                "x0": round(plant_observation.actual_x, 6),
                "command_issued": False,
                "command_count": 0,
                "command_success": False,
                "decision_sample_count": 0,
            })
            if not trace["command_issued"]:
                trace["decision_sample_count"] += 1
                predicted_center = applied_plan.expected_arrival_time
                window_half_width = known_config.dt / 2
                trace.update({
                    "decision_time": round(observation.time, 6),
                    "decision_time_sample_count": trace["decision_sample_count"],
                    "applied_eta": round(predicted_center, 6),
                    "clamped": correction.clamped,
                    "uncapped_time_delta": round(correction.uncapped_time_delta, 6),
                    "excess": round(correction.excess, 6),
                    "v_hat": round(correction.v_hat, 6),
                    "infeasible": correction.infeasible,
                    "window_remaining_time": round(
                        predicted_center + window_half_width - observation.time, 6
                    ),
                    "compensated_predicted_window": {
                        "start": round(predicted_center - window_half_width, 6),
                        "center": round(predicted_center, 6),
                        "end": round(predicted_center + window_half_width, 6),
                    },
                    # Each target's plant clock resets, so report the episode-global
                    # timestamp. Actions have zero modeled duration in this simulator.
                    "previous_object_grab_end_time": (
                        None if observation.target_id == 0
                        or observation.target_id - 1 not in object_grab_end_times
                        else round(object_grab_end_times[observation.target_id - 1], 6)
                    ),
                })
        if compensation:
            records.append({
                "time": round(observation.time, 6),
                "target_id": observation.target_id,
                "residual": round(residual, 6),
                "classification": disturbance,
                "position_delta": round(correction.position_delta, 6),
                "time_delta": round(correction.time_delta, 6),
                "uncapped_time_delta": round(correction.uncapped_time_delta, 6),
                "clamped": correction.clamped,
                "excess": round(correction.excess, 6),
                "v_hat": round(correction.v_hat, 6),
                "infeasible": correction.infeasible,
                "reason": correction.reason,
            })
        command_window_reached = (
            observation.time >= applied_plan.expected_arrival_time - known_config.dt / 2
        )
        if (
            compensation
            and correction.infeasible
            and command_window_reached
            and not safe_stop
            and observation.target_id not in attempted_targets
            and observation.target_id not in outcomes_by_target
        ):
            record_outcome(
                observation.target_id,
                "skipped",
                "correction_infeasible",
                observation.step,
                residual,
            )
        # Issue at the first sample at or beyond the window start. If sampling
        # jumps past the whole window, the controller evaluates the time error.
        if (not safe_stop and observation.target_id not in attempted_targets
                and observation.target_id not in outcomes_by_target
                and observation.time >= applied_plan.expected_arrival_time - known_config.dt / 2):
            command = Command(
                target_id=observation.target_id,
                speed=known_config.belt_speed,
                pick_position=applied_plan.pick_position,
                expected_time=applied_plan.expected_arrival_time,
                pick_y=known_config.y_pick,
            )
            response_delay = (
                plant_observation.response_delay
                if realization is not None
                else config.load_response_delay
                if config.scenario in ("load", "combo") and observation.step >= config.load_step
                else 0.0
            )
            delayed_x = plant_observation.actual_x + plant_observation.actual_speed * response_delay
            result = controller.execute_2d(
                command,
                delayed_x,
                plant_observation.actual_y,
                observation.time + response_delay,
            )
            if not plant_observation.target_present:
                result = replace(result, success=False, reason="target absent at execution")
            evaluator_row.update({
                "target_exists_at_execution": plant_observation.target_present,
                "command_issued": True,
                "execution_step": observation.step,
                "position_error": result.position_error,
            })
            policy_feedbacks.append(asdict(command_feedback(
                    command_id=f"{seed}:{observation.target_id}:{observation.step}",
                    target_id=observation.target_id,
                    issued_time=observation.time,
                    execution_time=observation.time + response_delay,
                    accepted=result.accepted,
                    success=result.accepted and result.success,
                )))
            attempted_targets.add(observation.target_id)
            if include_trace:
                trace_by_target[observation.target_id]["command_count"] += 1
            errors.append(result.position_error)
            successes += int(result.accepted and result.success)
            if result.accepted and result.success:
                record_outcome(observation.target_id, "picked", result.reason, observation.step, residual)
            elif result.accepted:
                record_outcome(observation.target_id, "attempt_failed", result.reason, observation.step, residual)
            else:
                record_outcome(observation.target_id, "rejected", result.reason, observation.step, residual)
            if include_trace:
                trace = trace_by_target[observation.target_id]
                trace.update({
                    "command_issued": True,
                    "command_success": bool(result.accepted and result.success),
                    "command_time": round(observation.time, 6),
                    "execution_time": round(observation.time + response_delay, 6),
                    "true_eta": round(
                        observation.time
                        + (config.x_pick - plant_observation.actual_x) / plant_observation.actual_speed,
                        6,
                    ),
                    "position_error": round(
                        ((delayed_x - applied_plan.pick_position) ** 2
                         + (plant_observation.actual_y - config.y_pick) ** 2) ** 0.5,
                        6,
                    ),
                    "time_error": round(
                        abs(observation.time + response_delay - applied_plan.expected_arrival_time)
                        * config.belt_speed,
                        6,
                    ),
                    "command_result": result.reason,
                    "skip_reason": (
                        None if result.accepted and result.success
                        else "command_issued_but_pick_failed"
                    ),
                })
            if result.accepted and result.success:
                object_grab_end_times[observation.target_id] = (
                    observation.target_id * config.episode_steps * config.dt
                    + observation.time + response_delay
                )
            if not result.accepted:
                safe_stop = True
                escalations.append({
                    "step": observation.step,
                    "target_id": observation.target_id,
                    "residual": residual,
                    "reason": result.reason,
                })
        world.advance()

    for target_id in range(config.object_count):
        if target_id not in outcomes_by_target:
            record_outcome(
                target_id,
                "skipped",
                "safe_stop_before_command" if safe_stop else "prediction_window_missed_before_command",
                config.episode_steps - 1,
                0.0,
            )

    outcomes = [outcomes_by_target[target_id] for target_id in sorted(outcomes_by_target)]
    terminal_counts = {
        state: sum(outcome["status"] == state for outcome in outcomes)
        for state in TERMINAL_STATES
    }

    total = max(1, config.object_count)
    receipt: dict[str, Any] = {
        "schema_version": "rra.receipt.v1",
        "config": config.model_dump(mode="json"),
        "seed": int(seed),
        "git_sha": git_sha or "unknown",
        "compensation": "on" if compensation else "off",
        "compensation_records": records,
        "policy_command_feedback": policy_feedbacks,
        "operational_text_context": text_context,
        "escalations": escalations,
        "outcomes": outcomes,
        "evaluator_objects": [evaluator_objects[key] for key in sorted(evaluator_objects)],
        "safe_stop": safe_stop,
        "metrics": {
            "attempted": len(attempted_targets),
            "successes": successes,
            "success_rate": round(successes / total, 6),
            "absolute_error_sum": round(sum(errors), 9),
            "mean_abs_error": round(sum(errors) / len(errors), 6) if errors else 0.0,
            "escalations": len(escalations),
            "terminal_counts": terminal_counts,
        },
    }
    if include_trace:
        failure_trace = []
        for target_id, trace in sorted(trace_by_target.items()):
            if trace["command_success"]:
                continue
            if not trace["command_issued"]:
                outcome = outcomes_by_target.get(target_id)
                if outcome is not None:
                    reason = outcome["reason"]
                elif safe_stop:
                    reason = "safe_stop_before_command"
                elif trace["window_remaining_time"] < 0:
                    reason = "prediction_window_expired_without_command"
                else:
                    reason = "prediction_window_not_reached_before_episode_end"
                trace["skip_reason"] = reason
            if target_id in outcomes_by_target:
                trace["terminal_status"] = outcomes_by_target[target_id]["status"]
            trace["seed"] = int(seed)
            trace["compensation"] = "on" if compensation else "off"
            trace["scenario"] = config.scenario
            failure_trace.append(trace)
        receipt["failure_trace"] = failure_trace
    hash_input = {key: value for key, value in receipt.items() if key != "git_sha"}
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt["receipt_sha256"] = sha256(canonical).hexdigest()
    return receipt
