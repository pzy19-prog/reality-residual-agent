"""Paired dev runner for B4 strict and text tie-break variants."""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
from rra.runtime import runtime_versions

from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.eval.runner import score_against_b1_denominators
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
from rra.llm.adapter import request_template_sha256
from rra.llm.providers import (NIM_MODEL, NvidiaNimProvider, ReplayCacheMiss,
                               ReplayProvider)

ROOT = Path(__file__).resolve().parents[3]


class _ReadThroughProvider:
    """Use the finalized-payload cache before making a live request."""
    def __init__(self, cache_dir: Path, *, replay_only: bool = False, format_mode: str = "json_object"):
        self.replay = ReplayProvider(cache_dir, model=NIM_MODEL, format_mode=format_mode)
        self.live = None if replay_only else NvidiaNimProvider(cache_dir=cache_dir, format_mode=format_mode)
        self.live_calls = 0
        self.requests_served = 0
        self.served_models: dict[str, int] = {}

    def _record_model(self, response: dict) -> None:
        model = response.get("model")
        if isinstance(model, str) and model:
            self.served_models[model] = self.served_models.get(model, 0) + 1

    @property
    def last_http_status(self):
        return None if self.live is None else self.live.last_http_status

    def complete(self, request_body: dict) -> dict:
        try:
            result = self.replay.complete(request_body)
            self.requests_served += 1
            self._record_model(result)
            return result
        except ReplayCacheMiss:
            if self.live is None:
                raise
            for attempt in range(3):
                try:
                    result = self.live.complete(request_body)
                    self.live_calls += 1
                    self.requests_served += 1
                    self._record_model(result)
                    return result
                except RuntimeError:
                    status = self.live.last_http_status
                    if status in (401, 403):
                        raise SystemExit(f"NVIDIA NIM HTTP {status}; stop Phase B")
                    if (status is not None and status < 500) or attempt == 2:
                        raise
                    time.sleep(2 ** attempt)


class _MemoizedProposer:
    """Share one proposal result between strict and tiebreak for equal inputs."""
    def __init__(self, proposer: HypothesisProposer):
        self.proposer = proposer
        self.cache: dict[str, Any] = {}

    def propose(self, evidence_packet: dict, context_text: str = "", *, s2_summary: dict | None = None):
        key = json.dumps({"evidence_packet": evidence_packet, "s2_summary": s2_summary},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        if key not in self.cache:
            self.cache[key] = self.proposer.propose(evidence_packet, context_text, s2_summary=s2_summary)
        return self.cache[key]


def _realization(index: int, seed: int):
    structures = composition_structures()
    case = index % 19
    return (realize_episode(seed, structures[case]) if case < len(structures)
            else realize_episode(seed, (), FAULT_FAMILIES[case - len(structures)]))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for variant in VARIANTS:
        variant_rows = [row for row in rows if row["text_variant"] == variant]
        out[variant] = {}
        for mode in ("B4_STRICT", "B4_TIEBREAK"):
            selected = [row[mode] for row in variant_rows]
            score = [row["scores"][mode] for row in variant_rows]
            unsafe_by_source = {"fast_layer_command": 0, "s2_authorized": 0}
            for row, scored in zip(selected, score):
                unsafe = set(scored["unsafe_target_ids"])
                source_by_target = {int(item["target_id"]): item.get("authorization_source", "fast_layer_command")
                                    for item in row["evaluator_objects"]}
                for target in unsafe:
                    key = source_by_target.get(int(target), "fast_layer_command")
                    unsafe_by_source[key] = unsafe_by_source.get(key, 0) + 1
            fallbacks: dict[str, int] = {}
            for item in selected:
                for decision in item.get("system2_decisions", []):
                    reason = decision.get("gate_reason", "")
                    if reason.startswith("TIEBREAK_FALLBACK:"):
                        key = reason.split(":", 1)[1]
                        fallbacks[key] = fallbacks.get(key, 0) + 1
            out[variant][mode] = {
                "episodes": len(selected),
                "recovery": sum(x["challenge_success_count"] for x in score),
                "pause_refusal": sum(len({int(decision["target_id"])
                                           for decision in item.get("system2_decisions", [])
                                           if decision.get("action") in
                                           ("PAUSE_AND_REOBSERVE", "HUMAN_ESCALATION")})
                                      for item in selected),
                "wrong_disposition": sum(x["wrong_disposition_count"] for x in score),
                "miss": sum(x["ordinary_miss_count"] for x in score),
                "unsafe_action": sum(x["unsafe_action_count"] for x in score),
                "unsafe_by_source": unsafe_by_source,
                "llm_calls": sum(x["llm_requests_served"] for x in variant_rows)
                             if mode == "B4_STRICT" else 0,
                "strict_proposer_invocations": sum(x["B4_STRICT"].get("strict_proposer_invocations", 0)
                                                    for x in variant_rows),
                "tiebreak_proposer_invocations": sum(x["B4_TIEBREAK"].get("tiebreak_proposer_invocations", 0)
                                                      for x in variant_rows),
                "TEXT_TIEBREAK": sum(d.get("gate_reason") == "TEXT_TIEBREAK"
                                     for x in selected for d in x.get("system2_decisions", [])),
                "fallbacks": fallbacks,
            }
    return out


def _decisions_sha256(decisions: list[dict[str, Any]]) -> str:
    body = json.dumps(decisions, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(body.encode()).hexdigest()


def _misleading_audit(row: dict[str, Any], mode: str) -> dict[str, Any]:
    receipt = row[mode]
    baseline_by_key = {(int(item["target_id"]), item["time"]): item
                       for item in row["B3"]["system2_decisions"]}
    outcome_by_target = {int(item["target_id"]): item for item in receipt["outcomes"]}
    truth_by_target = {int(item["target_id"]): item for item in receipt["evaluator_objects"]}
    disposition = row["scores"][mode]["dispositions"]
    cases = []
    for proposal in receipt.get("system2_proposal_rank", []):
        target = int(proposal["target_id"])
        first = next(iter(proposal.get("ranked_ids", [])), None)
        key = (target, proposal["time"])
        base = baseline_by_key.get(key, {})
        passing = {item.get("structure_id") for item in base.get("verifications", [])
                   if item.get("passed")}
        if first is None:
            relation = "no_valid_first_hypothesis"
        elif first not in passing:
            relation = "contradicted"
        elif mode == "B4_TIEBREAK":
            final_row = next((item for item in receipt.get("system2_decisions", [])
                              if int(item["target_id"]) == target and item["time"] == proposal["time"]), {})
            relation = ("selected" if final_row.get("tiebreak_selected_structure_id") == first
                        else "remained_ambiguous")
        else:
            relation = "remained_ambiguous"
        outcome = outcome_by_target.get(target, {})
        truth = truth_by_target.get(target, {})
        cases.append({
            "target_id": target, "time": proposal["time"],
            "first_hypothesis": first, "relation": relation,
            "final_disposition": disposition.get(str(target)),
            "recovery_result": outcome.get("status") == "picked"
                               and truth.get("position_error") is not None
                               and truth["position_error"] <= 0.2,
        })
    return {
        "wrong_disposition_count": row["scores"][mode]["wrong_disposition_count"],
        "unsafe_action_count": row["scores"][mode]["unsafe_action_count"],
        "pause_reobserve_count": len({int(item["target_id"]) for item in receipt.get("system2_decisions", [])
                                       if item.get("action") in
                                       ("PAUSE_AND_REOBSERVE", "HUMAN_ESCALATION")}),
        "cases": cases,
    }


def run_b4_dev(output_dir: Path = ROOT / "artifacts" / "s2", *,
               nproc: int | None = None, subset: bool = False,
               replay_only: bool = False, format_mode: str = "json_object") -> dict[str, Any]:
    """Run paired B4 modes for every dev episode and frozen text variant."""
    run_started = time.perf_counter()
    all_seeds = json.loads((ROOT / "config" / "dev_seeds.json").read_text())["seeds"]
    if subset:
        seeds = json.loads((ROOT / "artifacts" / "s2" / "diag-d1g.json").read_text())["seeds"]
    else:
        seeds = all_seeds
    index_by_seed = {seed: index for index, seed in enumerate(all_seeds)}
    config = v3_world_config("nominal")
    cache_dir = ROOT / "artifacts" / "llm_cache"
    baseline: dict[int, tuple[dict[str, Any], dict[str, Any], Any]] = {}
    n_amb = 0
    for seed in seeds:
        realization = _realization(index_by_seed[seed], seed)
        b1 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization)
        b3 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                         system2_enabled=True)
        n_amb += sum(not row.get("faults") and row.get("gate_reason") == "AMBIGUOUS"
                     for row in b3.get("system2_decisions", []))
        baseline[seed] = (b1, b3, realization)

    tasks = []
    for seed in seeds:
        realization = baseline[seed][2]
        cause = realization.fault_family or realization.structure
        contexts = freeze_episode_contexts(str(seed), seed, cause)
        for variant in VARIANTS:
            tasks.append((seed, variant, contexts[variant]))

    def run_task(task):
        seed, variant, frozen = task
        b1, b3, realization = baseline[seed]
        from rra.eval.context_v3 import verify_frozen_context
        verify_frozen_context(frozen)
        provider = _ReadThroughProvider(cache_dir, replay_only=replay_only, format_mode=format_mode)
        proposer = _MemoizedProposer(HypothesisProposer(provider))
        strict = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                             text_context=frozen.text, system2_enabled=True,
                             s2_variant="B4_STRICT", proposer=proposer)
        tie = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                           text_context=frozen.text, system2_enabled=True,
                           s2_variant="B4_TIEBREAK", proposer=proposer)
        if strict["system2_decisions"] != b3["system2_decisions"]:
            raise AssertionError(f"B-1 mismatch seed={seed} variant={variant}")
        scores = {
            "B4_STRICT": score_against_b1_denominators(strict, realization, config, b1),
            "B4_TIEBREAK": score_against_b1_denominators(tie, realization, config, b1),
        }
        return {
            "seed": seed, "text_variant": variant, "context_sha256": frozen.content_sha256,
            "B3_receipt_sha256": b3["receipt_sha256"],
            "B3": b3,
            "B4_STRICT": strict, "B4_TIEBREAK": tie, "scores": scores,
            "llm_requests_served": provider.requests_served,
            "live_llm_calls": provider.live_calls,
            "served_models": provider.served_models,
        }

    workers = max(1, min(nproc or min(4, os.cpu_count() or 1), len(tasks)))
    if workers == 1:
        rows = [run_task(task) for task in tasks]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(run_task, tasks))
    rows.sort(key=lambda row: (row["seed"], VARIANTS.index(row["text_variant"])))

    # Exercise the completed cache in both serial and parallel modes. These
    # replay-only passes make no additional network calls.
    sample = [task for task in tasks if task[0] in seeds[:3]]
    def replay_task(task):
        seed, variant, frozen = task
        b1, b3, realization = baseline[seed]
        provider = _ReadThroughProvider(cache_dir, replay_only=True, format_mode=format_mode)
        proposer = _MemoizedProposer(HypothesisProposer(provider))
        strict = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                             text_context=frozen.text, system2_enabled=True,
                             s2_variant="B4_STRICT", proposer=proposer)
        tie = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                           text_context=frozen.text, system2_enabled=True,
                           s2_variant="B4_TIEBREAK", proposer=proposer)
        return seed, variant, strict, tie
    serial_parallel_started = time.perf_counter()
    serial_sample = [replay_task(task) for task in sample]
    with ThreadPoolExecutor(max_workers=min(workers, max(1, len(sample)))) as pool:
        parallel_sample = list(pool.map(replay_task, sample))
    serial_by_key = {(seed, variant): (strict, tie) for seed, variant, strict, tie in serial_sample}
    parallel_by_key = {(seed, variant): (strict, tie) for seed, variant, strict, tie in parallel_sample}
    mismatches = []
    for key, expected in serial_by_key.items():
        actual = parallel_by_key[key]
        for mode in (0, 1):
            if (expected[mode]["receipt_sha256"] != actual[mode]["receipt_sha256"]
                    or expected[mode]["system2_decisions"] != actual[mode]["system2_decisions"]):
                mismatches.append({"seed": key[0], "variant": key[1], "mode": mode})
    if mismatches:
        raise RuntimeError(f"serial/parallel mismatch: {mismatches[0]}")
    serial_parallel_seconds = time.perf_counter() - serial_parallel_started

    compact = [{
        "seed": row["seed"], "text_variant": row["text_variant"],
        "context_sha256": row["context_sha256"], "B3_receipt_sha256": row["B3_receipt_sha256"],
        "B3_decision_count": len(baseline[row["seed"]][1]["system2_decisions"]),
        "B3_decisions_sha256": _decisions_sha256(baseline[row["seed"]][1]["system2_decisions"]),
        "B4_STRICT_receipt_sha256": row["B4_STRICT"]["receipt_sha256"],
        "B4_TIEBREAK_receipt_sha256": row["B4_TIEBREAK"]["receipt_sha256"],
        "B4_STRICT_decision_count": len(row["B4_STRICT"]["system2_decisions"]),
        "B4_TIEBREAK_decision_count": len(row["B4_TIEBREAK"]["system2_decisions"]),
        "strict_proposer_invocations": row["B4_STRICT"].get("strict_proposer_invocations", 0),
        "tiebreak_proposer_invocations": row["B4_TIEBREAK"].get("tiebreak_proposer_invocations", 0),
        "B4_STRICT_decisions_sha256": _decisions_sha256(row["B4_STRICT"]["system2_decisions"]),
        "B4_TIEBREAK_decisions_sha256": _decisions_sha256(row["B4_TIEBREAK"]["system2_decisions"]),
        "B4_STRICT_proposal_rank": row["B4_STRICT"].get("system2_proposal_rank", []),
        "B4_TIEBREAK_proposal_rank": row["B4_TIEBREAK"].get("system2_proposal_rank", []),
        "B4_STRICT_scores": {key: row["scores"]["B4_STRICT"][key] for key in (
            "challenge_success_count", "recoverable_challenge_count", "wrong_disposition_count",
            "ordinary_miss_count", "unsafe_action_count")},
        "B4_TIEBREAK_scores": {key: row["scores"]["B4_TIEBREAK"][key] for key in (
            "challenge_success_count", "recoverable_challenge_count", "wrong_disposition_count",
            "ordinary_miss_count", "unsafe_action_count")},
        **({"MISLEADING_TEXT_CONTEXT": {
            "B4_STRICT": _misleading_audit(row, "B4_STRICT"),
            "B4_TIEBREAK": _misleading_audit(row, "B4_TIEBREAK"),
        }} if row["text_variant"] == "MISLEADING_TEXT_CONTEXT" else {}),
        "llm_requests_served": row["llm_requests_served"],
    } for row in rows]
    served_models: dict[str, int] = {}
    for row in rows:
        for model, count in row["served_models"].items():
            served_models[model] = served_models.get(model, 0) + count
    body = {
        "schema_version": "rra.s2.b4-dev.v1", "subset": subset,
        "seed_identity": {"path": "artifacts/s2/diag-d1g.json" if subset else "config/dev_seeds.json",
                          "values": seeds},
        "episode_count": len(seeds), "text_variants": list(VARIANTS),
        "N_amb": n_amb, "estimated_llm_calls": round(4 * n_amb * 1.3, 1),
        "serial_parallel_check": {"consistent": True, "sample_pairs": len(sample)},
        "llm_requests_served": sum(row["llm_requests_served"] for row in rows),
        "llm_calls": sum(row["llm_requests_served"] for row in rows),
        "metrics": _summary(rows), "episodes": compact,
        "llm_request_spec": {
            "model": NIM_MODEL,
            "format_mode": format_mode,
            "max_tokens": 1800,
            "chat_template_kwargs": {"enable_thinking": False},
            "request_template_sha256": request_template_sha256({
                "model": NIM_MODEL, "format_mode": format_mode, "max_tokens": 1800,
                "chat_template_kwargs": {"enable_thinking": False},
            }),
        },
        "served_models": served_models,
        "runtime_versions": runtime_versions(),
        "operational_cost": {
            "live_llm_calls": sum(row["live_llm_calls"] for row in rows),
            "elapsed_seconds": time.perf_counter() - run_started,
            "nproc": workers,
            "serial_parallel_seconds": serial_parallel_seconds,
            "historical_live_run": {
                "source_commit": "92e2b89", "live_llm_calls": 376,
                "note": "transcribed from REPORT_D3_L5B.md",
            },
        },
    }
    hash_input = {key: value for key, value in body.items()
                  if key not in ("runtime_versions", "operational_cost")}
    body["receipt_sha256"] = sha256(json.dumps(hash_input, sort_keys=True,
                                                  separators=(",", ":")).encode()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "b4-dev.json").write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")
    return body
