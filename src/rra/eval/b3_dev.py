"""Dev-only paired B1-corrected and exhaustive B3 runner."""
from __future__ import annotations

import json
import multiprocessing as mp
import os
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any

from rra.eval.framework import v3_world_config
from rra.eval.runner import score_against_b1_denominators
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.eval.scoring import dispositions_for_episode
from rra.evidence import run_episode

ROOT = Path(__file__).resolve().parents[3]


def _unsafe_source_counts(unsafe_target_ids: list[int], evaluator_objects: list[dict[str, Any]]) -> dict[str, int]:
    source_by_target = {int(o["target_id"]): o.get("authorization_source", "fast_layer_command")
                        for o in evaluator_objects}
    return {
        "fast_layer_command": sum(source_by_target.get(int(t)) == "fast_layer_command" for t in unsafe_target_ids),
        "s2_authorized": sum(source_by_target.get(int(t)) == "s2_authorized" for t in unsafe_target_ids),
    }


def _preservation_regression_sources(
    target_ids: list[int], evaluator_objects: list[dict[str, Any]], fault_vetoes: list[dict[str, Any]],
) -> dict[str, int]:
    rows = {int(row["target_id"]): row for row in evaluator_objects}
    vetoed = {int(row["target_id"]) for row in fault_vetoes}
    counts = {"fault_veto": 0, "s2_authorized_action": 0, "other": 0}
    for target in target_ids:
        row = rows.get(int(target), {})
        if int(target) in vetoed:
            counts["fault_veto"] += 1
        elif row.get("authorization_source") == "s2_authorized":
            counts["s2_authorized_action"] += 1
        else:
            counts["other"] += 1
    return counts


def _run_seed(args: tuple[int, int]) -> dict[str, Any]:
    index, seed = args
    config = v3_world_config("nominal")
    structures = composition_structures()
    ix = index % 19
    if ix < len(structures):
        realization = realize_episode(seed, structures[ix])
    else:
        realization = realize_episode(seed, (), FAULT_FAMILIES[ix - len(structures)])
    b1 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization)
    b3 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                     system2_enabled=True)
    score = score_against_b1_denominators(b3, realization, config, b1)
    b1_score = score_against_b1_denominators(b1, realization, config, b1)
    labels = dispositions_for_episode(realization, config.object_count)
    auth = [d for d in b3.get("system2_decisions", []) if d["action"] == "UPDATE_MODEL_AND_REPLAN"]
    auth_count = len(auth) + sum(
        row.get("authorization") is not None for row in b3.get("system2_episode_authorizations", [])
    )
    refuse_n = sum(v == "REFUSE" for v in labels.values())
    refuse_correct = sum(
        v == "REFUSE" and not any(
            int(o["target_id"]) == k and o.get("command_issued") for o in b3["evaluator_objects"]
        ) for k, v in labels.items()
    )
    unsafe_ids = [int(t) for t in score["unsafe_target_ids"]]
    unsafe_by_source = _unsafe_source_counts(unsafe_ids, b3.get("evaluator_objects", []))
    preserve_ids = sorted(int(k) for k, v in score["dispositions"].items()
                          if b1["outcomes"][int(k)]["status"] == "picked" and v == "RECOVER")
    evaluator_by_target = {int(row["target_id"]): row for row in b3.get("evaluator_objects", [])}
    outcome_by_target = {int(row["target_id"]): row for row in b3.get("outcomes", [])}
    preservation_regression_ids = []
    for target in preserve_ids:
        row, outcome = evaluator_by_target.get(target, {}), outcome_by_target.get(target, {})
        success = (row.get("command_issued") and row.get("target_exists_at_execution") is not False
                   and outcome.get("status") == "picked"
                   and row.get("position_error") is not None
                   and row["position_error"] <= config.tolerance)
        if not success:
            preservation_regression_ids.append(target)
    preservation_by_source = _preservation_regression_sources(
        preservation_regression_ids, b3.get("evaluator_objects", []),
        b3.get("system2_fault_vetoes", []),
    )
    return {
        "seed": seed, "case": list(realization.structure), "fault_family": realization.fault_family,
        "b1_terminal_counts": b1["metrics"]["terminal_counts"],
        "b3_terminal_counts": b3["metrics"]["terminal_counts"], "score": score,
        "challenge_ids": sorted(int(k) for k, v in score["dispositions"].items()
                                 if b1["outcomes"][int(k)]["status"] != "picked"),
        "preservation_ids": preserve_ids,
        "refuse_total": refuse_n, "refuse_correct": refuse_correct,
        "authorizations": auth_count,
        "pause_target_ids": sorted({d["target_id"] for d in b3.get("system2_decisions", [])
                                     if d["action"] in ("PAUSE_AND_REOBSERVE", "HUMAN_ESCALATION")}),
        "system2_calls": b3.get("system2_calls", 0),
        "verifier_calls": b3.get("system2_verifier_calls", 0),
        "hypotheses_proposed": b3.get("system2_hypotheses_proposed", 0),
        "pause_seconds": b3.get("system2_wall_latency_seconds", 0.0),
        "miss_count": score["ordinary_miss_count"],
        "unsafe_by_source": unsafe_by_source,
        "preservation_regression_ids": preservation_regression_ids,
        "preservation_regression_by_source": preservation_by_source,
        "b1_unsafe_action_count": b1_score["unsafe_action_count"],
        "b1_receipt_sha256": b1["receipt_sha256"], "b3_receipt_sha256": b3["receipt_sha256"],
    }


def verify_serial_parallel(seeds: list[int], nproc: int) -> dict[str, Any]:
    sample = seeds[:3]
    args = list(enumerate(sample))
    start = perf_counter()
    serial = [_run_seed(arg) for arg in args]
    serial_seconds = perf_counter() - start
    start = perf_counter()
    with mp.Pool(processes=min(nproc, max(1, len(args)))) as pool:
        parallel = pool.map(_run_seed, args)
    parallel_seconds = perf_counter() - start
    serial_by_seed = {row["seed"]: row for row in serial}
    parallel_by_seed = {row["seed"]: row for row in parallel}
    mismatch = None
    for seed in sample:
        for field in ("b1_receipt_sha256", "b3_receipt_sha256"):
            if serial_by_seed[seed][field] != parallel_by_seed[seed][field]:
                mismatch = {"seed": seed, "field": field,
                            "serial": serial_by_seed[seed][field],
                            "parallel": parallel_by_seed[seed][field]}
                break
        if mismatch:
            break
    return {"seeds": sample, "consistent": mismatch is None, "first_mismatch": mismatch,
            "serial_seconds": serial_seconds, "parallel_seconds": parallel_seconds,
            "nproc": min(nproc, max(1, len(args)))}


def run_b3_dev(output_dir: Path = ROOT / "artifacts" / "s2", *, nproc: int | None = None) -> dict[str, Any]:
    """Run sorted dev seeds in worker processes after a three-seed parity check."""
    seeds = json.loads((ROOT / "config" / "dev_seeds.json").read_text())["seeds"]
    worker_count = max(1, min(nproc or min(8, os.cpu_count() or 1), len(seeds)))
    parity = verify_serial_parallel(seeds, worker_count)
    if not parity["consistent"]:
        raise RuntimeError(json.dumps(parity, sort_keys=True))
    args = list(enumerate(seeds))
    start = perf_counter()
    with mp.Pool(processes=worker_count) as pool:
        episodes = pool.map(_run_seed, args)
    parallel_wall_seconds = perf_counter() - start
    episodes.sort(key=lambda row: row["seed"])

    def summed(key: str) -> int:
        return sum(ep["score"][key] for ep in episodes)

    recoverable_challenge = sum(ep["score"]["recoverable_challenge_count"] for ep in episodes)
    challenge_success = sum(ep["score"]["challenge_success_count"] for ep in episodes)
    preservation = sum(ep["score"]["preservation_count"] for ep in episodes)
    refuse_n = sum(ep["refuse_total"] for ep in episodes)
    operational_cost = {
        "system2_calls": sum(ep["system2_calls"] for ep in episodes),
        "verifier_calls": sum(ep["verifier_calls"] for ep in episodes),
        "hypotheses_proposed": sum(ep["hypotheses_proposed"] for ep in episodes),
        "llm_calls": 0,
        "production_pause_seconds": sum(ep["pause_seconds"] for ep in episodes),
        "nproc": worker_count,
        "serial_parallel_check": parity,
        "parallel_full_dev_wall_seconds": parallel_wall_seconds,
        "per_seed": [{
            "seed": ep["seed"], "system2_calls": ep["system2_calls"],
            "verifier_calls": ep["verifier_calls"], "hypotheses_proposed": ep["hypotheses_proposed"],
            "llm_calls": 0, "production_pause_seconds": ep["pause_seconds"],
        } for ep in episodes],
    }
    for ep in episodes:
        ep.pop("pause_seconds", None)
    receipt = {
        "schema_version": "rra.s2.b3-dev.v1",
        "seed_identity": {"path": "config/dev_seeds.json", "values": seeds},
        "episode_count": len(episodes), "b1": "corrected", "b3": "exhaustive-14-structures",
        "metrics": {
            "recoverable_success": challenge_success / recoverable_challenge if recoverable_challenge else 0.0,
            "recoverable_challenge_success_count": challenge_success,
            "recoverable_challenge_count": recoverable_challenge,
            "pause_refusal": sum(len(ep["pause_target_ids"]) for ep in episodes),
            "correct_refuse_rate": sum(ep["refuse_correct"] for ep in episodes) / refuse_n if refuse_n else 0.0,
            "wrong_disposition": summed("wrong_disposition_count"), "miss": summed("ordinary_miss_count"),
            "unsafe_action": summed("unsafe_action_count"),
            "unsafe_action_by_source": {
                source: sum(ep["unsafe_by_source"][source] for ep in episodes)
                for source in ("fast_layer_command", "s2_authorized")
            },
            "b1_corrected_unsafe_action": sum(ep["b1_unsafe_action_count"] for ep in episodes),
            "preservation_regression_count": summed("preservation_regression_count"),
            "preservation_regression_by_source": {
                source: sum(ep["preservation_regression_by_source"][source] for ep in episodes)
                for source in ("fault_veto", "s2_authorized_action", "other")
            },
            "preservation_count": preservation, "authorization_count": sum(ep["authorizations"] for ep in episodes),
        },
        "operational_cost": operational_cost,
        "episodes": episodes,
    }
    hash_input = {key: value for key, value in receipt.items() if key != "operational_cost"}
    receipt["receipt_sha256"] = sha256(json.dumps(hash_input, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "b3-dev.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    m, c = receipt["metrics"], receipt["operational_cost"]
    md = [
        "# B1-corrected vs B3 — dev seeds", "",
        f"Seeds: {len(seeds)} from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.", "",
        "| Metric | B3 dev |", "|---|---:|",
        f"| Recoverable challenge success | {m['recoverable_success']:.4f} ({m['recoverable_challenge_success_count']}/{m['recoverable_challenge_count']}) |",
        f"| Correct refusal rate | {m['correct_refuse_rate']:.4f} |",
        f"| Wrong disposition | {m['wrong_disposition']} |", f"| Miss | {m['miss']} |",
        f"| Unsafe action | {m['unsafe_action']} |",
        f"| Unsafe: fast layer command | {m['unsafe_action_by_source']['fast_layer_command']} |",
        f"| Unsafe: S2 authorized | {m['unsafe_action_by_source']['s2_authorized']} |",
        f"| B1-corrected unsafe action (same episodes) | {m['b1_corrected_unsafe_action']} |",
        f"| Preservation regression | {m['preservation_regression_count']}/{m['preservation_count']} |",
        f"| Preservation regression by cause | fault veto {m['preservation_regression_by_source']['fault_veto']}; S2 authorized action {m['preservation_regression_by_source']['s2_authorized_action']}; other {m['preservation_regression_by_source']['other']} |",
        f"| Authorizations | {m['authorization_count']} |", "", "## Operational cost", "",
        f"- System-2 calls: {c['system2_calls']}", f"- Verifier calls: {c['verifier_calls']}",
        f"- Hypotheses proposed: {c['hypotheses_proposed']}", f"- LLM calls: {c['llm_calls']}",
        f"- Production pause seconds: {c['production_pause_seconds']:.3f}",
        f"- Serial / parallel three-seed wall time: {parity['serial_seconds']:.3f} / {parity['parallel_seconds']:.3f} s",
        f"- Full parallel run wall time: {parallel_wall_seconds:.3f} s with nproc={worker_count}", "",
        f"Receipt SHA-256: `{receipt['receipt_sha256']}`", "",
    ]
    (output_dir / "b3-dev.md").write_text("\n".join(md))
    return receipt
