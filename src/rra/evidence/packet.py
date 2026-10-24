"""Canonical, policy-whitelisted evidence packets for L3."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


C1_KNOWN_CONFIG_FIELDS = ("dt", "tolerance", "x_pick", "y_pick", "belt_speed")


def project_c1_known_config(known_config: dict[str, Any]) -> dict[str, Any]:
    """Project L3's stored config row to the five policy-visible C1 fields."""
    return {key: known_config[key] for key in C1_KNOWN_CONFIG_FIELDS}


def build_packet(*, episode_id: str, target_id: int, step: int, time: float,
                 observations: Iterable[dict[str, Any]], presence_events: Iterable[dict[str, Any]],
                 command_feedback: Iterable[dict[str, Any]], known_config: dict[str, Any],
                 context: dict[str, str], episode_steps: int = 100) -> dict[str, Any]:
    seq = int(target_id) * int(episode_steps) + int(step)
    def key(row: dict[str, Any]) -> tuple[int, int]:
        return (int(row.get("target_id", -1)), int(row.get("seq", -1)))
    obs = sorted((r for r in observations if int(r["target_id"]) == target_id and int(r["seq"]) <= seq), key=key)
    pres = sorted((r for r in presence_events if int(r["target_id"]) == target_id and int(r["seq"]) <= seq), key=key)
    feedback = sorted((r for r in command_feedback if int(r["seq"]) < seq), key=key)
    return {
        "schema": "rra.evidence_packet.v1",
        "observations": obs,
        "presence_events": pres,
        "command_feedback": feedback,
        "known_config": known_config,
        "context": context,
        "decision": {"episode_id": str(episode_id), "target_id": int(target_id),
                     "step": int(step), "time": time, "seq": seq},
    }


def canonical(packet: dict[str, Any]) -> str:
    return json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def packet_sha256(packet: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(packet).encode("utf-8")).hexdigest()
