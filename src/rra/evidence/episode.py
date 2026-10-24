"""Episode runner and JSON-compatible evidence receipt."""

from __future__ import annotations

from hashlib import sha256
import json
import platform
from time import perf_counter
from dataclasses import asdict, replace
from functools import partial
from typing import Any, Literal

import numpy as np
from rra.runtime import runtime_versions

from rra.controller import Command, Controller, ControllerConfig
from rra.fast import Corrector, ResidualMonitor
from rra.planner import ScriptedPlanner
from rra.evidence.policy import (
    command_feedback,
    sanitize_config,
    sanitize_observation,
    target_presence_event,
)
from rra.evidence.packet import build_packet, project_c1_known_config
from rra.s2.b3 import run_b3
from rra.s2.dsl import Action, FaultHypothesis, structure_id as registered_structure_id
from rra.s2.fitter import Observation as S2Observation, CommandFeedback as S2Feedback, fit as fit_hypothesis
from rra.s2.verifier import verify as verify_hypothesis
from rra.s2.dsl import structures as registered_structures
from rra.s2.faults import check_faults
from rra.s2.authorization import authorize
from rra.s2.prediction import pick_error_at_command_time, predicted_residual_at_time
from rra.s2.verifier import common_action
from rra.sim import World, WorldConfig
from rra.eval.scenarios import EpisodeRealization
from rra.sim.v3_world import V3World

TERMINAL_STATES = ("picked", "attempt_failed", "rejected", "escalated", "skipped")
CONSECUTIVE_OUTCOME_FAILURE_THRESHOLD = 3
# A05 §1.2: retry on the first observation at or after the 0.5 s deadline.
REOBSERVE_RETRY_EPSILON = 1e-9


def _verification_structure_id(value: Any) -> str | None:
    try:
        return getattr(value, "structure_id", None) or registered_structure_id(value.structure)
    except (AttributeError, ValueError):
        return None


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
    system2_enabled: bool = False,
    include_s2_diagnostics: bool = False,
    s2_variant: Literal["B3", "B4_STRICT", "B4_TIEBREAK"] = "B3",
    proposer: Any | None = None,
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
    policy_observation_samples: list[dict[str, Any]] = []
    policy_target_presence_events: list[dict[str, Any]] = []
    canonical_presence_events: list[dict[str, Any]] = []
    system2_observations: dict[int, list[S2Observation]] = {}
    system2_overrides: dict[int, float] = {}
    system2_execution_etas: dict[int, float] = {}
    system2_authorized: set[int] = set()
    active_target_authorizations: dict[int, dict[str, Any]] = {}
    system2_paused: set[int] = set()
    system2_next_retry: dict[int, float] = {}
    system2_reobserve_holds: dict[int, str] = {}
    reobserve_hold_entries = 0
    reobserve_retry_count = 0
    reobserve_authorized_count = 0
    reobserve_exhausted_count = 0
    reobserve_end_reasons = {name: 0 for name in (
        "authorized", "window_end", "latch", "target_switch", "s2_non_pause", "episode_end",
    )}
    system2_receipts: list[dict[str, Any]] = []
    system2_authorization_events: list[dict[str, Any]] = []
    system2_wall_latency_seconds = 0.0
    system2_verifier_calls = 0
    system2_hypotheses_proposed = 0
    system2_calls = 0
    strict_proposer_invocations = 0
    tiebreak_proposer_invocations = 0
    system2_infeasible_attempted: set[int] = set()
    system2_escalation_active: set[int] = set()
    system2_fault_vetoes: dict[int, dict[str, Any]] = {}
    hard_fault_latch: dict[str, Any] = {"latched": False, "latched_at": None, "events": []}
    hard_fault_latch_categories: set[str] = set()
    hard_fault_decision_targets: set[int] = set()
    outcome_escalation_pending = False
    outcome_escalation_active = False
    outcome_escalation_attempts = 0
    outcome_retry_at_global: float | None = None
    active_episode_authorization: dict[str, Any] | None = None
    episode_authorization_history: list[dict[str, Any]] = []
    current_global_time = 0.0
    first_observed_at: dict[int, float] = {}
    first_s2_sample_count: dict[int, int] = {}
    s2_diagnostic_calls: list[dict[str, Any]] = []
    s2_proposal_rank: list[dict[str, Any]] = []

    if s2_variant not in ("B3", "B4_STRICT", "B4_TIEBREAK"):
        raise ValueError(f"unknown System-2 variant: {s2_variant}")
    if s2_variant in ("B4_STRICT", "B4_TIEBREAK") and proposer is None:
        raise ValueError(f"{s2_variant} requires a proposer")

    def policy_exception_for(observation: Any, residual: float, correction: Any,
                             action_time: float | None) -> dict[str, float]:
        exception: dict[str, float] = {}
        plan = base_plans.get(observation.target_id)
        if action_time is not None and plan is not None:
            delta = float(action_time - plan.expected_arrival_time)
            if abs(delta) > fast_time_limit:
                exception["time_correction_seconds"] = delta
        if abs(residual) > fast_residual_threshold:
            exception["residual_above_threshold"] = float(residual)
        if safe_stop:
            exception["safe_stop_clear"] = 1.0
        return exception

    def revoke_authorization(target_id: int, record: dict[str, Any], when: float,
                             evidence_ids: list[str],
                             reason: str = "POST_VERIFICATION_CHANGE") -> None:
        nonlocal active_episode_authorization
        record["revoked_at"] = when
        record["expires_reason"] = reason
        record["revocation_evidence_ids"] = evidence_ids
        system2_authorized.discard(target_id)
        system2_escalation_active.discard(target_id)
        system2_overrides.pop(target_id, None)
        system2_execution_etas.pop(target_id, None)
        active_target_authorizations.pop(target_id, None)
        if record.get("episode_level") and active_episode_authorization is not None:
            active_episode_authorization["target_ids"].discard(target_id)
            auth_id = record["authorization"]["authorization_id"]
            for history in episode_authorization_history:
                if history["authorization"]["authorization_id"] == auth_id:
                    history.setdefault("target_revocations", []).append({
                        "target_id": target_id, "revoked_at": when,
                        "global_time": current_global_time,
                        "reason": reason,
                        "authorization_id": auth_id,
                        "evidence_ids": evidence_ids,
                    })
            if not active_episode_authorization["target_ids"]:
                active_episode_authorization["expired_at_global"] = when
                active_episode_authorization["expires_reason"] = reason
                active_episode_authorization = None
        system2_authorization_events.append({
            "time": when, "target_id": target_id, "event": "REVOKE_AUTHORIZATION",
            "reason": reason, "revoked_at": when, "global_time": current_global_time,
            "authorization_id": record["authorization"]["authorization_id"],
            "evidence_ids": evidence_ids,
        })

    def positive_fault_veto(b3: dict[str, Any], target_id: int,
                            observations: list[S2Observation],
                            presence_events: list[dict[str, Any]]) -> dict[str, Any] | None:
        registered_vetoes = {
            FaultHypothesis.SENSOR_STUCK,
            FaultHypothesis.BELT_STOP_OR_MOTION_LOSS,
            FaultHypothesis.OBJECT_MISSING_OR_DROPPED,
        }
        faults = [fault for fault in b3["faults"] if fault in registered_vetoes]
        if b3["action"] is Action.HUMAN_ESCALATION:
            faults.extend(fault for fault in b3["faults"] if fault not in faults
                          and fault is not FaultHypothesis.UNKNOWN_OR_INSUFFICIENT_EVIDENCE)
        if not faults:
            return None
        checks = []
        for fault in faults:
            if fault is FaultHypothesis.OBJECT_MISSING_OR_DROPPED:
                evidence_ids = [
                    f"presence:{target_id}:{event['time']:.3f}"
                    for event in presence_events
                    if event["target_id"] == target_id and not event.get("target_observed", True)
                ]
            else:
                window = b3.get("fault_evidence_windows", {}).get(fault, observations)
                evidence_ids = [f"obs:{target_id}:{item.time:.3f}" for item in window]
            checks.append({"check_item": fault.value, "evidence_ids": evidence_ids})
        record = {"target_id": target_id, "check_items": checks}
        system2_fault_vetoes[target_id] = record
        return record

    def hard_fault_veto_record(target_id: int) -> dict[str, Any]:
        return {
            "target_id": target_id,
            "check_items": [{
                "check_item": event["category"],
                "evidence_ids": list(event["evidence_ids"]),
            } for event in hard_fault_latch["events"]],
        }

    def record_latched_human_escalation(target_id: int, when: float) -> None:
        if not system2_enabled or not hard_fault_latch["latched"]:
            return
        veto = hard_fault_veto_record(target_id)
        system2_fault_vetoes[target_id] = veto
        if target_id not in hard_fault_decision_targets:
            hard_fault_decision_targets.add(target_id)
            system2_receipts.append({
                "time": when, "target_id": target_id, "trigger": "hard_fault_latch",
                "action": Action.HUMAN_ESCALATION.value,
                "gate_reason": "HARD_FAULT_LATCH",
                "faults": [item["category"] for item in hard_fault_latch["events"]],
                "fault_veto": veto, "pause_seconds": 0.0,
            })

    def latch_hard_fault(category: str, target_id: int, when: float,
                         evidence_ids: list[str]) -> None:
        nonlocal safe_stop
        if not system2_enabled:
            return
        if category not in hard_fault_latch_categories:
            hard_fault_latch_categories.add(category)
            hard_fault_latch["events"].append({
                "category": category, "time": when,
                "global_time": current_global_time,
                "target_id": target_id, "evidence_ids": list(evidence_ids),
            })
        if not hard_fault_latch["latched"]:
            hard_fault_latch["latched"] = True
            hard_fault_latch["latched_at"] = when
            hard_fault_latch["latched_at_global"] = current_global_time
            safe_stop = True
            for authorized_target, record in list(active_target_authorizations.items()):
                revoke_authorization(authorized_target, record, when, evidence_ids,
                                     reason="HARD_FAULT_LATCH")
            if episode_authorization_history:
                history = episode_authorization_history[-1]
                if history.get("revoked_at") is None and active_episode_authorization is None:
                    history["revoked_at"] = when
                    history["expires_reason"] = "HARD_FAULT_LATCH"
        for future_target in range(target_id, config.object_count):
            system2_fault_vetoes[future_target] = hard_fault_veto_record(future_target)
        record_latched_human_escalation(target_id, when)

    def latch_from_faults(faults: Any, target_id: int, when: float,
                          evidence_ids: list[str], fault_windows: dict | None = None) -> None:
        latchable = {
            FaultHypothesis.SENSOR_STUCK,
            FaultHypothesis.BELT_STOP_OR_MOTION_LOSS,
            FaultHypothesis.OBJECT_MISSING_OR_DROPPED,
        }
        for fault in faults:
            if fault in latchable:
                window = (fault_windows or {}).get(fault)
                supporting_ids = [f"obs:{target_id}:{item.time:.3f}" for item in window] if window else evidence_ids
                if fault is FaultHypothesis.OBJECT_MISSING_OR_DROPPED:
                    supporting_ids = evidence_ids
                if not supporting_ids and fault in {
                    FaultHypothesis.SENSOR_STUCK,
                    FaultHypothesis.BELT_STOP_OR_MOTION_LOSS,
                }:
                    supporting_ids = evidence_ids
                latch_hard_fault(fault.value, target_id, when, supporting_ids)

    def record_outcome(
        target_id: int,
        status: str,
        reason: str,
        step: int,
        residual: float,
    ) -> None:
        nonlocal consecutive_outcome_failures, safe_stop
        nonlocal outcome_escalation_pending, outcome_escalation_active
        nonlocal outcome_retry_at_global, active_episode_authorization
        if target_id in outcomes_by_target:
            return
        outcomes_by_target[target_id] = {
            "target_id": target_id,
            "status": status,
            "reason": reason,
        }
        evaluator_objects.setdefault(target_id, {"target_id": target_id})["terminal_status"] = status
        terminal_authorization = active_target_authorizations.pop(target_id, None)
        if terminal_authorization is not None:
            terminal_authorization["revoked_at"] = current_global_time
            terminal_authorization["expires_reason"] = "target_terminal"
            system2_authorized.discard(target_id)
            system2_authorization_events.append({
                "time": current_global_time, "target_id": target_id,
                "event": "TARGET_TERMINAL", "reason": "target_terminal",
                "authorization_id": terminal_authorization["authorization"]["authorization_id"],
            })
        if (active_episode_authorization is not None
                and target_id in active_episode_authorization["target_ids"]
                and status in ("attempt_failed", "rejected", "skipped")):
            active_episode_authorization["expired_at_global"] = current_global_time
            active_episode_authorization["expires_reason"] = "next_authorized_failure_result"
            episode_authorization_history[-1]["revoked_at"] = current_global_time
            episode_authorization_history[-1]["expires_reason"] = "next_authorized_failure_result"
            for scoped_target in system2_authorized.copy():
                if scoped_target in episode_authorization_history[-1]["target_ids"]:
                    system2_authorized.discard(scoped_target)
            active_episode_authorization = None
            safe_stop = True
            outcome_escalation_active = True
            outcome_escalation_pending = outcome_escalation_attempts < 3
            outcome_retry_at_global = current_global_time
        if (terminal_authorization is not None and terminal_authorization.get("episode_level")
                and active_episode_authorization is not None
                and target_id in active_episode_authorization["target_ids"]):
            active_episode_authorization["target_ids"].discard(target_id)
            auth_id = terminal_authorization["authorization"]["authorization_id"]
            for history in episode_authorization_history:
                if history["authorization"]["authorization_id"] == auth_id:
                    history.setdefault("target_terminal_events", []).append({
                        "target_id": target_id, "time": current_global_time,
                    })
            if not active_episode_authorization["target_ids"]:
                active_episode_authorization["expired_at_global"] = current_global_time
                active_episode_authorization["expires_reason"] = "all_targets_terminal"
                active_episode_authorization = None
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
                if system2_enabled:
                    outcome_escalation_active = True
                    outcome_escalation_pending = outcome_escalation_attempts < 3
                    outcome_retry_at_global = current_global_time
        else:
            consecutive_outcome_failures = 0

    def finish_reobserve_hold(target_id: int, step: int, residual: float, end_reason: str) -> None:
        nonlocal reobserve_exhausted_count
        reason = system2_reobserve_holds.pop(target_id, None)
        if reason is None:
            return
        reobserve_end_reasons[end_reason] += 1
        reobserve_exhausted_count += 1
        terminal_reason = f"{reason};REOBSERVE_EXHAUSTED"
        record_outcome(target_id, "escalated", terminal_reason, step, residual)
        escalations.append({"step": step, "target_id": target_id,
                            "residual": residual, "reason": terminal_reason})

    def run_outcome_escalation(observation: Any) -> None:
        nonlocal outcome_escalation_pending, outcome_escalation_attempts
        nonlocal active_episode_authorization, safe_stop, system2_wall_latency_seconds
        nonlocal system2_calls, system2_verifier_calls, system2_hypotheses_proposed
        nonlocal outcome_escalation_active, outcome_retry_at_global
        if (not system2_enabled or not outcome_escalation_pending
                or outcome_escalation_attempts >= 3):
            return
        target_id = observation.target_id
        if hard_fault_latch["latched"]:
            record_latched_human_escalation(target_id, observation.time)
            outcome_escalation_pending = False
            outcome_escalation_active = True
            safe_stop = True
            return
        s2obs = system2_observations.get(target_id, [])
        prediction_error = partial(
            pick_error_at_command_time, observation=observation,
            nominal_speed=known_config.belt_speed, x_pick=known_config.x_pick,
        )
        pause_started = perf_counter()
        b3 = run_b3(
            s2obs, nominal_speed=known_config.belt_speed,
            feedback=[S2Feedback(x["issued_time"], x["execution_time"], x["accepted"], x["success"])
                      for x in policy_feedbacks],
            evidence_refs=[f"obs:{target_id}:{o.time:.3f}" for o in s2obs],
            current_time=observation.time, dt=known_config.dt,
            horizon=(config.episode_steps - 1) * config.dt,
            tolerance=known_config.tolerance, error=prediction_error,
            presence_events=[e for e in policy_target_presence_events if e["target_id"] == target_id],
        )
        system2_wall_latency_seconds += perf_counter() - pause_started
        outcome_escalation_attempts += 1
        system2_calls += 1
        system2_verifier_calls += len(b3["verifications"])
        system2_hypotheses_proposed += len(b3["fits"])
        evidence_ids = [f"obs:{target_id}:{o.time:.3f}" for o in s2obs]
        latch_from_faults(b3["faults"], target_id, observation.time, evidence_ids,
                          b3.get("fault_evidence_windows"))
        fault_veto = (hard_fault_veto_record(target_id) if hard_fault_latch["latched"]
                      else positive_fault_veto(b3, target_id, s2obs, policy_target_presence_events))
        chosen = next((h for h in b3["passing"]
                       if prediction_error(h, b3["action_time"] or observation.time) <= known_config.tolerance), None)
        if hard_fault_latch["latched"]:
            chosen = None
            b3["action"] = Action.HUMAN_ESCALATION
            b3["gate_reason"] = "HARD_FAULT_LATCH"
        auth = None
        exception = {}
        if chosen is not None:
            if abs(observation.observed_x - observation.nominal_x) > fast_residual_threshold:
                exception["residual_above_threshold"] = float(observation.observed_x - observation.nominal_x)
            if b3["action_time"] is not None and target_id in base_plans:
                delta = float(b3["action_time"] - base_plans[target_id].expected_arrival_time)
                if abs(delta) > fast_time_limit:
                    exception["time_correction_seconds"] = delta
            if safe_stop:
                exception["safe_stop_clear"] = 1.0
        if (not hard_fault_latch["latched"]
                and b3["action"] is Action.UPDATE_MODEL_AND_REPLAN and chosen is not None
                and not b3["faults"] and exception):
            scope_ids = sorted(set(range(observation.target_id, config.object_count)) - set(outcomes_by_target))
            scope = "episode_targets:" + ",".join(map(str, scope_ids))
            expires = (config.object_count * config.episode_steps) * config.dt
            auth = authorize(
                episode_id=str(seed), hypothesis_id=chosen.hypothesis_id,
                evidence_ids=[f"obs:{target_id}:{o.time:.3f}" for o in s2obs],
                parameters=chosen.fitted_parameters, score=chosen.rmse,
                action=Action.UPDATE_MODEL_AND_REPLAN, scope=scope,
                expires_at=expires, exception=exception,
                terminal_condition="next_authorized_failure_or_model_contradiction",
            )
            active_episode_authorization = {"authorization": asdict(auth), "target_ids": set(scope_ids),
                                            "parameters": dict(chosen.fitted_parameters)}
            episode_authorization_history.append({"time": observation.time, "authorization": asdict(auth),
                                                  "target_ids": scope_ids, "revoked_at": None,
                                                  "target_revocations": []})
            for scoped_target in scope_ids:
                if scoped_target == target_id and b3["action_time"] is not None:
                    system2_overrides[scoped_target] = float(b3["action_time"])
                    system2_execution_etas[scoped_target] = float(b3["action_time"])
                system2_authorized.add(scoped_target)
                active_target_authorizations[scoped_target] = {
                    "authorization": asdict(auth),
                    "structure": list(chosen.structure),
                    "episode_level": True,
                }
            outcome_escalation_active = False
            outcome_escalation_pending = False
            if not hard_fault_latch["latched"]:
                safe_stop = False
        else:
            outcome_escalation_pending = outcome_escalation_attempts < 3
            outcome_retry_at_global = current_global_time + 0.5
            safe_stop = True
        system2_receipts.append({
            "time": observation.time, "target_id": target_id, "trigger": "outcome_escalation",
            "action": b3["action"].value, "gate_reason": b3["gate_reason"],
            "faults": [f.value for f in b3["faults"]],
            "fault_veto": fault_veto,
            "authorization": asdict(auth) if auth is not None else None,
            "attempt": outcome_escalation_attempts, "pause_seconds": 0.0,
            "verifications": [{"hypothesis_id": v.hypothesis_id,
                               "structure_id": _verification_structure_id(v),
                               "structure": list(v.structure),
                               "parameters": v.fitted_parameters, "rmse": v.rmse, "passed": v.passed}
                              for v in b3["verifications"]],
        })
        if include_s2_diagnostics:
            first_s2_sample_count.setdefault(target_id, len(s2obs))
            s2_diagnostic_calls.append({
                "seed": int(seed), "target_id": target_id, "sim_time": observation.time,
                "first_observed_at": first_observed_at.get(target_id),
                "window_remaining_time": max(0.0, base_plans.get(target_id, planner.plan(
                    observation, known_config.belt_speed, known_config.x_pick)).expected_arrival_time
                    + known_config.dt / 2 - observation.time),
                "n_usable_before_upgrade": first_s2_sample_count[target_id],
                "n_usable_after_upgrade": max(0, len(s2obs) - first_s2_sample_count[target_id]),
                "n_usable_total": len(s2obs),
                "fits": [{"structure": [p.value for p in f.structure], "fit": not f.no_fit,
                          "rmse": f.objective, "n_usable": f.n_usable, "parameters": f.parameters}
                         for f in b3["fits"]],
                "decision_observation": {"time": observation.time, "observed_x": observation.observed_x,
                                         "nominal_x": observation.nominal_x,
                                         "nominal_speed": known_config.belt_speed},
                "verified": [{"structure_id": _verification_structure_id(v),
                              "structure": list(v.structure), "rmse": v.rmse,
                              "n_usable": v.n_usable, "passed": v.passed} for v in b3["verifications"]],
                "passing": [list(v.structure) for v in b3["passing"]], "gate": b3["gate_reason"],
                "action_time": b3["action_time"], "faults": [f.value for f in b3["faults"]],
                "action": b3["action"].value, "trigger": "outcome_escalation",
            })

    for _ in range(config.episode_steps * config.object_count):
        plant_observation = world.observation()
        current_global_time = (plant_observation.target_id * config.episode_steps + plant_observation.step) * config.dt
        evaluator_row = evaluator_objects.setdefault(plant_observation.target_id, {
            "target_id": plant_observation.target_id,
            "target_exists_at_execution": None,
            "command_issued": False,
            "execution_step": None,
            "position_error": None,
            "stale_authorization": False,
        })
        # One registered detector event is emitted for every expected sample,
        # including samples where no positional observation is available.
        presence_event = asdict(target_presence_event(
            target_id=plant_observation.target_id,
            step=plant_observation.step,
            time=plant_observation.time,
            target_observed=plant_observation.target_present,
        ))
        seq = plant_observation.target_id * config.episode_steps + plant_observation.step
        policy_target_presence_events.append(presence_event)
        canonical_presence_events.append({"episode_id": str(seed), "seq": seq, **presence_event})
        if system2_enabled and not plant_observation.target_present:
            latch_hard_fault(
                FaultHypothesis.OBJECT_MISSING_OR_DROPPED.value,
                plant_observation.target_id, plant_observation.time,
                [f"presence:{plant_observation.target_id}:{plant_observation.time:.3f}"],
            )
            if hard_fault_latch["latched"]:
                for held_target in list(system2_reobserve_holds):
                    finish_reobserve_hold(held_target, plant_observation.step, 0.0, "latch")
        if not plant_observation.target_present:
            if (system2_enabled and hard_fault_latch["latched"]
                    and plant_observation.target_id not in outcomes_by_target):
                record_outcome(plant_observation.target_id, "escalated", "HARD_FAULT_LATCH",
                               plant_observation.step, 0.0)
                safe_stop = True
            # The detector event remains visible; positional data never reaches policy.
            world.advance()
            continue
        observation = sanitize_observation(plant_observation)
        policy_observation_samples.append({"episode_id": str(seed), "seq": seq, **asdict(observation)})
        if active_target != observation.target_id:
            if active_target in system2_reobserve_holds:
                finish_reobserve_hold(active_target, observation.step, 0.0, "target_switch")
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
        system2_observations.setdefault(observation.target_id, []).append(
            S2Observation(observation.time, observation.observed_x, observation.nominal_x)
        )
        first_observed_at.setdefault(observation.target_id, observation.time)
        evidence_ids = [f"obs:{observation.target_id}:{item.time:.3f}"
                        for item in system2_observations[observation.target_id]]
        if system2_enabled:
            observed_fault_result = check_faults(
                system2_observations[observation.target_id],
                nominal_speed=known_config.belt_speed, dt=known_config.dt,
                presence_events=[event for event in policy_target_presence_events
                                 if event["target_id"] == observation.target_id],
                return_windows=True,
            )
            if (isinstance(observed_fault_result, tuple) and len(observed_fault_result) == 2
                    and isinstance(observed_fault_result[1], dict)):
                observed_faults, observed_fault_windows = observed_fault_result
            else:  # Compatibility with test doubles and downstream detector overrides.
                observed_faults, observed_fault_windows = observed_fault_result, {}
            latch_from_faults(observed_faults, observation.target_id,
                              observation.time, evidence_ids, observed_fault_windows)
            if hard_fault_latch["latched"]:
                safe_stop = True
                record_latched_human_escalation(observation.target_id, observation.time)
                for held_target in list(system2_reobserve_holds):
                    finish_reobserve_hold(held_target, observation.step, 0.0, "latch")
        authorization_record = active_target_authorizations.get(observation.target_id)
        if system2_enabled and authorization_record is not None:
            authorization = authorization_record["authorization"]
            structure = next((candidate for candidate in registered_structures()
                              if tuple(item.value for item in candidate)
                              == tuple(authorization_record["structure"])), None)
            verified = None
            if structure is not None:
                fitted = fit_hypothesis(
                    structure, system2_observations[observation.target_id],
                    nominal_speed=known_config.belt_speed,
                    feedback=[S2Feedback(x["issued_time"], x["execution_time"], x["accepted"], x["success"])
                              for x in policy_feedbacks],
                )
                verified = verify_hypothesis(
                    fitted, hypothesis_id=authorization["hypothesis_id"],
                    evidence_refs=evidence_ids,
                )
            faults = check_faults(
                system2_observations[observation.target_id],
                nominal_speed=known_config.belt_speed, dt=known_config.dt,
                presence_events=[event for event in policy_target_presence_events
                                 if event["target_id"] == observation.target_id],
            )
            positive_faults = [fault for fault in faults
                               if fault is not FaultHypothesis.UNKNOWN_OR_INSUFFICIENT_EVIDENCE]
            if verified is not None and verified.passed and not positive_faults:
                system2_authorization_events.append({
                    "time": observation.time, "target_id": observation.target_id,
                    "event": "POST_VERIFICATION_PASS",
                    "hypothesis_id": authorization["hypothesis_id"],
                    "n_usable": verified.n_usable, "rmse": verified.rmse,
                    "evidence_ids": evidence_ids,
                })
            if verified is None or not verified.passed or positive_faults:
                if positive_faults:
                    system2_fault_vetoes[observation.target_id] = {
                        "target_id": observation.target_id,
                        "check_items": [{"check_item": fault.value, "evidence_ids": evidence_ids}
                                        for fault in positive_faults],
                    }
                    safe_stop = True
                revoke_authorization(observation.target_id, authorization_record,
                                     observation.time, evidence_ids)
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
        recovered_by_s2 = False
        if (outcome_escalation_pending and outcome_retry_at_global is not None
                and current_global_time >= outcome_retry_at_global):
            run_outcome_escalation(observation)
        hold_due = (observation.target_id in system2_reobserve_holds
                    and observation.time >= system2_next_retry.get(observation.target_id, float("inf"))
                    - REOBSERVE_RETRY_EPSILON)
        if hold_due:
            window_end = (base_plan.expected_arrival_time + known_config.dt / 2)
            if window_end - observation.time <= 0:
                finish_reobserve_hold(observation.target_id, observation.step, residual, "window_end")
                hold_due = False
            else:
                reobserve_retry_count += 1
        escalating = "ESCALATE:" in correction.reason
        if not escalating:
            system2_escalation_active.discard(observation.target_id)
        escalation_event = escalating and observation.target_id not in system2_escalation_active
        s2_action = None
        if (system2_enabled and not hard_fault_latch["latched"] and (escalation_event or hold_due
                or (correction.infeasible and observation.target_id not in system2_infeasible_attempted))
                and observation.time >= system2_next_retry.get(observation.target_id, -1.0)
                - REOBSERVE_RETRY_EPSILON):
            if escalation_event:
                system2_escalation_active.add(observation.target_id)
            if correction.infeasible:
                system2_infeasible_attempted.add(observation.target_id)
            s2obs = system2_observations[observation.target_id]
            prediction_error = partial(
                pick_error_at_command_time,
                observation=observation,
                nominal_speed=known_config.belt_speed,
                x_pick=known_config.x_pick,
            )
            pause_started=perf_counter()
            b3 = run_b3(
                s2obs, nominal_speed=known_config.belt_speed,
                feedback=[S2Feedback(x["issued_time"], x["execution_time"], x["accepted"], x["success"]) for x in policy_feedbacks],
                evidence_refs=[f"obs:{observation.target_id}:{o.time:.3f}" for o in s2obs],
                current_time=observation.time, dt=known_config.dt,
                horizon=(config.episode_steps-1)*config.dt,
                tolerance=known_config.tolerance, error=prediction_error,
                presence_events=[e for e in policy_target_presence_events if e["target_id"]==observation.target_id],
            )
            if (s2_variant in ("B4_STRICT", "B4_TIEBREAK")
                    and not b3["faults"] and b3["gate_reason"] == "AMBIGUOUS"):
                evidence_packet = build_packet(
                    episode_id=str(seed), target_id=observation.target_id, step=observation.step,
                    time=observation.time, observations=policy_observation_samples,
                    presence_events=canonical_presence_events,
                    command_feedback=[
                        {"episode_id": str(seed),
                         "seq": int(item["target_id"]) * config.episode_steps
                                + int(str(item["command_id"]).rsplit(":", 1)[1]),
                         "step": int(str(item["command_id"]).rsplit(":", 1)[1]), **item}
                        for item in policy_feedbacks
                    ],
                    known_config=project_c1_known_config(asdict(known_config)),
                    context={"text": text_context,
                             "content_sha256": sha256(text_context.encode("utf-8")).hexdigest()},
                    episode_steps=config.episode_steps,
                )
                s2_summary = {
                    "passing": [{"structure_id": _verification_structure_id(item),
                                 "rmse": float(item.rmse), "n_usable": int(item.n_usable)}
                                for item in b3["passing"]],
                    "current_time": float(observation.time),
                    "horizon": float((config.episode_steps - 1) * config.dt),
                }
                if s2_variant == "B4_STRICT":
                    strict_proposer_invocations += 1
                else:
                    tiebreak_proposer_invocations += 1
                proposal = proposer.propose(evidence_packet, "", s2_summary=s2_summary)
                provider_status = getattr(getattr(proposer, "provider", None), "last_http_status", None)
                if provider_status in (401, 403):
                    raise SystemExit(f"NVIDIA NIM HTTP {provider_status}; stop Phase B")
                # Keep receipts free of provider error bodies or other raw text.
                raw_error_type = proposal.error.split(":", 1)[0] if proposal.error else None
                proposal_error = (
                    "INVALID_PROPOSAL"
                    if raw_error_type in {"ValueError", "TypeError", "ValidationError", "JSONDecodeError"}
                    else "PROVIDER_ERROR" if raw_error_type else None
                )
                ranked_ids = [] if proposal is None else [item.hypothesis_id for item in proposal.items]
                s2_proposal_rank.append({
                    "time": observation.time, "target_id": observation.target_id,
                    "ranked_ids": ranked_ids,
                    "unknown_ids": [] if proposal is None else proposal.receipt.get("unknown_ids", []),
                    "error": proposal_error,
                })
                if s2_variant == "B4_TIEBREAK":
                    if proposal_error:
                        b3["gate_reason"] = f"TIEBREAK_FALLBACK:{proposal_error}"
                    else:
                        passing_by_id = {_verification_structure_id(item): item for item in b3["passing"]}
                        fault_ids = {fault.value for fault in FaultHypothesis}
                        selected = None
                        fault_before_selected = False
                        for item_id in ranked_ids:
                            if item_id in fault_ids:
                                fault_before_selected = True
                                break
                            if item_id in passing_by_id:
                                selected = passing_by_id[item_id]
                                break
                        if fault_before_selected:
                            b3["gate_reason"] = "TIEBREAK_FALLBACK:FAULT_ID"
                        elif proposal is not None and proposal.receipt.get("unknown_ids"):
                            b3["gate_reason"] = "TIEBREAK_FALLBACK:UNKNOWN_ID"
                        elif selected is None:
                            b3["gate_reason"] = "TIEBREAK_FALLBACK:NO_PROPOSED_PASSING_STRUCTURE"
                        else:
                            tie_action, tie_time, tie_reason = common_action(
                                [selected], current_time=observation.time, dt=known_config.dt,
                                horizon=(config.episode_steps - 1) * config.dt,
                                tolerance=known_config.tolerance, error=prediction_error,
                            )
                            if tie_action is Action.UPDATE_MODEL_AND_REPLAN:
                                b3["action"] = tie_action
                                b3["action_time"] = tie_time
                                b3["gate_reason"] = "TEXT_TIEBREAK"
                                b3["tiebreak_selected"] = selected
                            else:
                                b3["gate_reason"] = f"TIEBREAK_FALLBACK:{tie_reason}"
            s2_action = b3["action"]
            system2_wall_latency_seconds += perf_counter()-pause_started
            system2_calls += 1
            system2_verifier_calls += len(b3["verifications"])
            system2_hypotheses_proposed += len(b3["fits"])
            latch_from_faults(
                b3["faults"], observation.target_id, observation.time,
                [f"obs:{observation.target_id}:{o.time:.3f}" for o in s2obs],
                b3.get("fault_evidence_windows"),
            )
            fault_veto = positive_fault_veto(
                b3, observation.target_id, s2obs, policy_target_presence_events
            )
            if hard_fault_latch["latched"]:
                fault_veto = hard_fault_veto_record(observation.target_id)
                b3["action"] = Action.HUMAN_ESCALATION
                b3["gate_reason"] = "HARD_FAULT_LATCH"
            if fault_veto is not None or hard_fault_latch["latched"]:
                safe_stop = True
            if include_s2_diagnostics:
                first_s2_sample_count.setdefault(observation.target_id, len(s2obs))
                n_pre = first_s2_sample_count[observation.target_id]
                s2_diagnostic_calls.append({
                    "seed": int(seed), "target_id": observation.target_id,
                    "sim_time": observation.time,
                    "first_observed_at": first_observed_at[observation.target_id],
                    "window_remaining_time": max(0.0, base_plans[observation.target_id].expected_arrival_time
                                                 + known_config.dt / 2 - observation.time),
                    "planned_window_end": base_plans[observation.target_id].expected_arrival_time
                                         + known_config.dt / 2,
                    "n_usable_before_upgrade": n_pre,
                    "n_usable_after_upgrade": max(0, len(s2obs) - n_pre),
                    "n_usable_total": len(s2obs),
                    "fits": [{"structure": [p.value for p in f.structure], "fit": not f.no_fit,
                              "rmse": f.objective, "n_usable": f.n_usable,
                              "parameters": f.parameters} for f in b3["fits"]],
                    "decision_observation": {"time": observation.time, "observed_x": observation.observed_x,
                                             "nominal_x": observation.nominal_x,
                                             "nominal_speed": known_config.belt_speed},
                    "verified": [{"structure_id": _verification_structure_id(v),
                                  "structure": list(v.structure), "rmse": v.rmse,
                                  "n_usable": v.n_usable, "passed": v.passed}
                                 for v in b3["verifications"]],
                    "passing": [list(v.structure) for v in b3["passing"]],
                    "gate": b3["gate_reason"], "action_time": b3["action_time"],
                    "faults": [f.value for f in b3["faults"]],
                    "action": b3["action"].value,
                })
            chosen = b3.get("tiebreak_selected") or next(
                (h for h in b3["passing"]
                 if prediction_error(h, b3["action_time"] or observation.time) <= known_config.tolerance),
                None,
            )
            exception = policy_exception_for(observation, residual, correction, b3["action_time"])
            if hard_fault_latch["latched"]:
                chosen = None
                record_latched_human_escalation(observation.target_id, observation.time)
            if (not hard_fault_latch["latched"]
                    and b3["action"] is Action.UPDATE_MODEL_AND_REPLAN and chosen is not None
                    and not b3["faults"] and exception):
                system2_overrides[observation.target_id]=float(b3["action_time"])
                system2_execution_etas[observation.target_id]=float(b3["action_time"])
                system2_authorized.add(observation.target_id)
                system2_paused.discard(observation.target_id)
                recovered_by_s2=True
                authorization=authorize(
                    episode_id=str(seed), hypothesis_id=chosen.hypothesis_id,
                    evidence_ids=[f"obs:{observation.target_id}:{o.time:.3f}" for o in s2obs],
                    parameters=chosen.fitted_parameters, score=chosen.rmse,
                    action=Action.UPDATE_MODEL_AND_REPLAN,
                    scope=f"target:{observation.target_id}",
                    expires_at=(observation.target_id+1)*config.episode_steps*config.dt,
                    exception=exception,
                )
                active_target_authorizations[observation.target_id] = {
                    "authorization": asdict(authorization),
                    "structure": list(chosen.structure),
                }
                system2_receipts.append({
                    "time":observation.time,"target_id":observation.target_id,
                    "action":b3["action"].value,"gate_reason":b3["gate_reason"],
                    "fault_veto":fault_veto,
                    "hypothesis_id":chosen.hypothesis_id,
                    "structure_id":_verification_structure_id(chosen),
                    "structure":list(chosen.structure),
                    "fitted_parameters":chosen.fitted_parameters,"n_usable":chosen.n_usable,
                    "rmse":chosen.rmse,"residual_vector":list(chosen.residual_vector),
                    "violated_invariants":list(chosen.violated_invariants),"passed":chosen.passed,
                    "evidence_refs":list(chosen.evidence_refs),"common_action_time":b3["action_time"],
                    "authorization":asdict(authorization),"pause_seconds":0.0,
                    **({"tiebreak_selected_structure_id": _verification_structure_id(b3["tiebreak_selected"])}
                       if b3.get("tiebreak_selected") is not None else {}),
                })
            else:
                system2_receipts.append({
                    "time":observation.time,"target_id":observation.target_id,
                    "action":b3["action"].value,"gate_reason":b3["gate_reason"],
                    "faults":[f.value for f in b3["faults"]],"fault_veto":fault_veto,"pause_seconds":0.0,
                    "verifications":[{
                        "hypothesis_id":v.hypothesis_id,
                        "structure_id":_verification_structure_id(v),
                        "structure":list(v.structure),
                        "fitted_parameters":v.fitted_parameters,"n_usable":v.n_usable,
                        "rmse":v.rmse,"residual_vector":list(v.residual_vector),
                        "violated_invariants":list(v.violated_invariants),"passed":v.passed,
                        "evidence_refs":list(v.evidence_refs),
                    } for v in b3["verifications"]],
                    **({"tiebreak_selected_structure_id": _verification_structure_id(b3["tiebreak_selected"])}
                       if b3.get("tiebreak_selected") is not None else {}),
                })
                if b3["action"] is Action.PAUSE_AND_REOBSERVE:
                    system2_paused.add(observation.target_id)
                    system2_next_retry[observation.target_id]=observation.time+0.5
                    if observation.target_id in system2_reobserve_holds:
                        safe_stop = True
            if (observation.target_id in system2_reobserve_holds
                    and s2_action is not None
                    and s2_action is not Action.PAUSE_AND_REOBSERVE
                    and observation.target_id not in system2_authorized):
                finish_reobserve_hold(observation.target_id, observation.step, residual, "s2_non_pause")
            if (observation.target_id in system2_reobserve_holds
                    and observation.target_id in system2_authorized):
                system2_reobserve_holds.pop(observation.target_id, None)
                reobserve_end_reasons["authorized"] += 1
                reobserve_authorized_count += 1
                if not system2_reobserve_holds and not hard_fault_latch["latched"]:
                    safe_stop = False
        if "ESCALATE:" in correction.reason and observation.target_id not in system2_authorized:
            if (system2_enabled and not hard_fault_latch["latched"]
                    and observation.target_id not in outcomes_by_target
                    and s2_action is Action.PAUSE_AND_REOBSERVE):
                if observation.target_id not in system2_reobserve_holds:
                    reobserve_hold_entries += 1
                system2_reobserve_holds.setdefault(observation.target_id, correction.reason)
                system2_next_retry[observation.target_id] = observation.time + 0.5
                safe_stop = True
            elif observation.target_id in system2_reobserve_holds:
                if s2_action is not None:
                    finish_reobserve_hold(observation.target_id, observation.step, residual, "s2_non_pause")
            else:
                record_outcome(
                    observation.target_id, "escalated", correction.reason,
                    observation.step, residual,
                )
                if not safe_stop:
                    escalations.append({"step": observation.step,"target_id": observation.target_id,"residual": residual,"reason": correction.reason})
                safe_stop = True
        applied_plan = correction.plan if compensation else nominal_plan
        if observation.target_id in system2_overrides:
            applied_plan = applied_plan.model_copy(update={"expected_arrival_time":system2_overrides[observation.target_id]})
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
            and not hard_fault_latch["latched"]
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
        if (not safe_stop and not hard_fault_latch["latched"]
                and observation.target_id not in attempted_targets
                and observation.target_id not in outcomes_by_target
                and observation.time >= applied_plan.expected_arrival_time - known_config.dt / 2):
            command = Command(
                target_id=observation.target_id,
                speed=known_config.belt_speed,
                pick_position=applied_plan.pick_position,
                expected_time=system2_execution_etas.get(observation.target_id, applied_plan.expected_arrival_time),
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
            if system2_enabled:
                evaluator_row["authorization_global_time"] = current_global_time
                evaluator_row["authorization_source"] = (
                    "s2_authorized" if observation.target_id in system2_authorized
                    else "fast_layer_command"
                )
                if observation.target_id in system2_authorized:
                    evaluator_row["authorization_id"] = active_target_authorizations[
                        observation.target_id
                    ]["authorization"]["authorization_id"]
            if include_s2_diagnostics:
                diagnostic = next((row for row in reversed(s2_diagnostic_calls)
                                   if row["target_id"] == observation.target_id), None)
                if diagnostic is not None:
                    diagnostic["actual_x_at_execution"] = delayed_x
                    diagnostic["execution_time"] = observation.time + response_delay
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

    for target_id in list(system2_reobserve_holds):
        finish_reobserve_hold(target_id, config.episode_steps - 1, 0.0, "episode_end")
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
        "policy_target_presence_events": policy_target_presence_events,
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
        "runtime_versions": runtime_versions(),
    }
    if system2_enabled:
        receipt["system2_decisions"] = system2_receipts
        receipt["system2_reobserve"] = {
            "hold_entries": reobserve_hold_entries,
            "reobservations": reobserve_retry_count,
            "authorized_after_hold": reobserve_authorized_count,
            "exhausted": reobserve_exhausted_count,
            "end_reasons": reobserve_end_reasons,
        }
        receipt["system2_authorization_events"] = system2_authorization_events
        receipt["system2_hard_fault_latch"] = hard_fault_latch
        receipt["system2_episode_authorizations"] = episode_authorization_history
        receipt["system2_fault_vetoes"] = [system2_fault_vetoes[key]
                                           for key in sorted(system2_fault_vetoes)]
        # Operational pause telemetry is intentionally excluded from the deterministic hash.
        receipt["system2_wall_latency_seconds"] = round(system2_wall_latency_seconds, 6)
        receipt["system2_verifier_calls"] = system2_verifier_calls
        receipt["system2_hypotheses_proposed"] = system2_hypotheses_proposed
        receipt["system2_calls"] = system2_calls
        if s2_variant in ("B4_STRICT", "B4_TIEBREAK"):
            receipt["strict_proposer_invocations"] = strict_proposer_invocations
            receipt["tiebreak_proposer_invocations"] = tiebreak_proposer_invocations
    if s2_variant in ("B4_STRICT", "B4_TIEBREAK"):
        receipt["s2_variant"] = s2_variant
        receipt["system2_proposal_rank"] = s2_proposal_rank
    if include_s2_diagnostics:
        for row in s2_diagnostic_calls:
            outcome = outcomes_by_target.get(row["target_id"])
            row["terminal_status"] = outcome["status"] if outcome else None
            row["terminal_reason"] = outcome["reason"] if outcome else None
            truth_row = evaluator_objects.get(row["target_id"], {})
            row["command_issued"] = bool(truth_row.get("command_issued"))
            row["unsafe_witness"] = truth_row.get("position_error")
        receipt["s2_diagnostic_trace"] = s2_diagnostic_calls
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
    hash_input = {key: value for key, value in receipt.items() if key not in (
        "git_sha", "system2_wall_latency_seconds", "system2_verifier_calls",
        "system2_hypotheses_proposed", "system2_calls", "s2_diagnostic_trace", "runtime_versions")}
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt["receipt_sha256"] = sha256(canonical).hexdigest()
    return receipt
