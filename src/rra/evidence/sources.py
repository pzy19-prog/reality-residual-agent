"""Whitelisted source export, reference replay, and fail-closed schema checks."""
from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rra.evidence.packet import build_packet, packet_sha256
from rra.evidence.policy import sanitize_observation
from rra.eval.context_v3 import VARIANTS, freeze_context
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.evidence import run_episode
from rra.sim.v3_world import V3World

C1 = {
    "observation_samples": {"episode_id", "seq", "target_id", "step", "time", "observed_x", "observed_y", "nominal_x", "nominal_y", "nominal_speed"},
    "presence_events": {"episode_id", "seq", "target_id", "step", "time", "target_observed"},
    "command_feedback": {"episode_id", "seq", "step", "command_id", "target_id", "issued_time", "execution_time", "accepted", "success", "reason_code"},
    "known_config": {"episode_id", "dt", "tolerance", "x_pick", "y_pick", "belt_speed", "episode_steps", "object_count"},
    "ops_context": {"episode_id", "text", "content_sha256"},
}


def check_whitelist(schemas: dict[str, Any], rows: dict[str, list[dict[str, Any]]] | None = None) -> None:
    errors = []
    for table, allowed in C1.items():
        names = schemas.get(table, [])
        if isinstance(names, dict):
            names = names.keys()
        extra = sorted(set(names) - allowed)
        missing = sorted(allowed - set(names))
        if extra or missing:
            errors.append(f"{table}: extra={extra}, missing={missing}")
        for i, row in enumerate((rows or {}).get(table, [])):
            extra_row = sorted(set(row) - allowed)
            if extra_row:
                errors.append(f"{table}[{i}] extra={extra_row}")
    unknown = sorted(set(schemas) - set(C1))
    if unknown:
        errors.append(f"unknown tables={unknown}")
    if errors:
        raise ValueError("whitelist FAIL: " + "; ".join(errors))


def episode_case(index: int) -> tuple[int, Any]:
    structures = composition_structures()
    case = index % 19
    if case < len(structures):
        return case, realize_episode(index, structures[case])
    return case, realize_episode(index, (), FAULT_FAMILIES[case - len(structures)])


def export_sources(out: Path, episodes: int = 20) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    tables = {name: [] for name in C1}
    audits = []
    config = v3_world_config("nominal")
    for i in range(episodes):
        seed = i
        case, realization = episode_case(i)
        receipt = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                              system2_enabled=True, include_s2_diagnostics=True)
        variant = VARIANTS[i % 4]
        cause = realization.fault_family or realization.structure
        frozen = freeze_context(str(seed), seed, variant, cause)
        episode_id = str(seed)
        presence = []
        for row in receipt["policy_target_presence_events"]:
            seq = row["target_id"] * config.episode_steps + row["step"]
            presence.append({"episode_id": episode_id, "seq": seq, **row})
        world = V3World(config, seed, realization)
        observations = []
        for _ in range(config.object_count * config.episode_steps):
            raw = world.observation()
            if raw.target_present:
                row = asdict(sanitize_observation(raw))
                seq = row["target_id"] * config.episode_steps + row["step"]
                observations.append({"episode_id": episode_id, "seq": seq, **row})
            world.advance()
        feedback = []
        for row in receipt["policy_command_feedback"]:
            target = int(row["target_id"])
            try:
                step = int(str(row["command_id"]).rsplit(":", 1)[1])
            except (IndexError, ValueError):
                if "step" not in row:
                    raise ValueError("command feedback requires an explicit step when command_id omits it")
                step = int(row["step"])
            feedback.append({"episode_id": episode_id, "seq": target * config.episode_steps + step,
                             "step": step, **row})
        known = {"episode_id": episode_id, **config.model_dump(include={"dt", "tolerance", "x_pick", "y_pick", "belt_speed", "episode_steps", "object_count"})}
        ctx = {"episode_id": episode_id, "text": frozen.text, "content_sha256": frozen.content_sha256}
        tables["observation_samples"].extend(observations)
        tables["presence_events"].extend(presence)
        tables["command_feedback"].extend(feedback)
        tables["known_config"].append(known)
        tables["ops_context"].append(ctx)
        ref_rollup = hashlib.sha256()
        for presence_row in sorted(presence, key=lambda row: row["seq"]):
            target, step = presence_row["target_id"], presence_row["step"]
            packet = build_packet(episode_id=episode_id, target_id=target, step=step,
                                  time=presence_row["time"], observations=observations,
                                  presence_events=presence, command_feedback=feedback,
                                  known_config={k:v for k,v in known.items() if k != "episode_id"},
                                  context={"text": frozen.text, "content_sha256": frozen.content_sha256},
                                  episode_steps=config.episode_steps)
            ref_rollup.update(packet_sha256(packet).encode("ascii"))
        diagnostics = receipt.get("s2_diagnostic_trace", [])
        mismatches = [d for d in diagnostics if len([o for o in observations if o["target_id"] == d["target_id"] and o["time"] <= d["sim_time"]]) != d["n_usable_total"]]
        authids = [d.get("authorization", {}).get("evidence_ids") for d in receipt.get("system2_decisions", []) if d.get("authorization")]
        audits.append({"seed":seed,"case":case,"variant":variant,"decision_points":len(presence),"hard_fault_latch_decisions":sum(x.get("trigger")=="hard_fault_latch" for x in receipt.get("system2_decisions",[])),"mismatches":len(mismatches),"auth_evidence_nonempty":all(bool(x) for x in authids),"packets_sha256_rollup":ref_rollup.hexdigest(),"s2_diagnostic_trace":diagnostics,"system2_decisions":receipt.get("system2_decisions",[])})
    check_whitelist({k: set().union(*(r.keys() for r in v)) if v else C1[k] for k,v in tables.items()}, tables)
    for name, rows in tables.items():
        with (out / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    return {"tables":tables,"audits":audits}


def load_packets(tables: dict[str, list[dict[str, Any]]], episode_id: str) -> list[dict[str, Any]]:
    scoped = {k:[r for r in tables[k] if r["episode_id"] == episode_id] for k in C1}
    known = {k:v for k,v in scoped["known_config"][0].items() if k != "episode_id"}
    ctx = {k:v for k,v in scoped["ops_context"][0].items() if k != "episode_id"}
    steps = int(known["episode_steps"])
    return [build_packet(episode_id=episode_id, target_id=row["target_id"], step=row["step"], time=row["time"],
                         observations=scoped["observation_samples"], presence_events=scoped["presence_events"],
                         command_feedback=scoped["command_feedback"], known_config=known, context=ctx,
                         episode_steps=steps)
            for row in sorted(scoped["presence_events"], key=lambda item: item["seq"])]
