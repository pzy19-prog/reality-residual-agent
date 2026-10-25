#!/usr/bin/env python3
"""Probe registered B4 output-format modes on deterministic dev-seed requests."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
from typing import Any

from rra.eval.b4_dev import _realization
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer, proposal_request, request_template_sha256
from rra.llm.providers import NIM_MODEL, NvidiaNimProvider, finalize_payload, request_sha256
from rra.runtime import runtime_versions

ROOT = Path(__file__).resolve().parents[1]
FORMAT_MODES = ("json_object", "json_schema", "nvext_guided_json")
SELECTION_RULE = "A06 §3.2 / A07 §3.2"


class _CaptureProposer:
    def __init__(self):
        self.requests: list[dict[str, Any]] = []

    def propose(self, evidence_packet, context_text="", *, s2_summary=None):
        self.requests.append({"evidence_packet": evidence_packet, "s2_summary": s2_summary})
        return type("ProposalResult", (), {"items": [], "error": None,
                                            "receipt": {"unknown_ids": []}})()


def _provider_settings(mode: str) -> dict[str, Any]:
    return {"model": NIM_MODEL, "format_mode": mode, "max_tokens": 1800,
            "chat_template_kwargs": {"enable_thinking": False}}


def _cache_key(entry: dict[str, Any], mode: str) -> str:
    request = proposal_request(entry["evidence_packet"], entry["s2_summary"])
    return request_sha256(finalize_payload(request, _provider_settings(mode)))


def _collect_requests(k: int) -> list[dict[str, Any]]:
    seeds = json.loads((ROOT / "artifacts/s2/diag-d1g.json").read_text())["seeds"]
    dev_seeds = json.loads((ROOT / "config/dev_seeds.json").read_text())["seeds"]
    index_by_seed = {seed: index for index, seed in enumerate(dev_seeds)}
    config = v3_world_config("nominal")
    collected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for seed in seeds:
        realization = _realization(index_by_seed[seed], seed)
        cause = realization.fault_family or realization.structure
        contexts = freeze_episode_contexts(str(seed), seed, cause)
        for variant in VARIANTS:
            capture = _CaptureProposer()
            run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                        text_context=contexts[variant].text, system2_enabled=True,
                        s2_variant="B4_STRICT", proposer=capture)
            for entry in capture.requests:
                key = _cache_key(entry, "json_object")
                if key in seen:
                    continue
                seen.add(key)
                collected.append(entry)
                if len(collected) >= k:
                    return collected
    return collected


def _receipt_hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _select_format_mode(results: dict[str, dict[str, Any]]) -> str:
    return max(
        FORMAT_MODES,
        key=lambda mode: (results[mode]["valid_nonempty_items"], -FORMAT_MODES.index(mode)),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--live", action="store_true")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--max-calls", type=int, default=30)
    args = parser.parse_args(argv)
    if args.k < 1 or args.max_calls < 1 or args.k * len(FORMAT_MODES) > args.max_calls:
        parser.error("K must be positive and K × 3 must not exceed --max-calls")
    requests = _collect_requests(args.k)
    total_calls = len(requests) * len(FORMAT_MODES)
    if total_calls > args.max_calls:
        parser.error("collected probe calls exceed --max-calls")
    cache_keys = {mode: [_cache_key(row, mode) for row in requests] for mode in FORMAT_MODES}
    if args.dry_run:
        print(json.dumps({"probe_requests": len(requests), "format_modes": {
            mode: len(requests) for mode in FORMAT_MODES}, "live_calls": total_calls,
            "cache_keys": cache_keys}, indent=2))
        return 0
    out = ROOT / "artifacts/s2/b4-probe.json"
    if out.exists():
        parser.error(f"refusing to overwrite existing probe artifact: {out}")
    if not os.environ.get("NVIDIA_API_KEY"):
        parser.error("--live requires NVIDIA_API_KEY")

    results = {}
    for mode in FORMAT_MODES:
        provider = NvidiaNimProvider(cache_dir=ROOT / "artifacts/llm_probe_cache" / mode,
                                     format_mode=mode)
        finish_reasons: Counter[str] = Counter()
        valid = http_errors = 0
        latencies: list[float] = []
        served_models: Counter[str] = Counter()
        for row in requests:
            proposer = HypothesisProposer(provider)
            # Metadata belongs to one request only; failed calls must not inherit
            # the previous response body's model or finish_reason.
            provider.last_response_body = None
            provider.last_http_status = None
            proposal = proposer.propose(row["evidence_packet"], "", s2_summary=row["s2_summary"])
            response = provider.last_response_body
            finish_reason = "error_record"
            if proposal.error is not None and response is None:
                finish_reasons["error_record"] += 1
            else:
                response = response or {}
                choice = (response.get("choices") or [{}])[0]
                finish_reason = str(choice.get("finish_reason", "missing"))
                finish_reasons[finish_reason] += 1
            if isinstance(response, dict) and isinstance(response.get("model"), str):
                served_models[response["model"]] += 1
            valid += int(proposal.error is None and bool(proposal.items)
                         and finish_reason != "length")
            http_errors += int(provider.last_http_status is not None and provider.last_http_status >= 400)
            if provider.last_latency_seconds is not None:
                latencies.append(float(provider.last_latency_seconds))
        results[mode] = {
            "valid_nonempty_items": valid,
            "finish_reason_distribution": dict(sorted(finish_reasons.items())),
            "http_errors": http_errors,
            "average_latency_seconds": statistics.mean(latencies) if latencies else 0.0,
            "served_models": dict(sorted(served_models.items())),
            "request_count": len(requests),
        }
    body = {
        "schema_version": "rra.s2.b4-probe.v1",
        "seed_role": "dev_diag_only",
        "seed_source": "artifacts/s2/diag-d1g.json",
        "probe_request_count": len(requests), "max_calls": args.max_calls,
        "request_template_sha256": {
            mode: request_template_sha256(_provider_settings(mode)) for mode in FORMAT_MODES
        },
        "modes": results,
        "runtime_versions": runtime_versions(),
    }
    selected_format_mode = _select_format_mode(results)
    body["selected_format_mode"] = selected_format_mode
    body["selection_rule"] = SELECTION_RULE
    hash_body = {key: value for key, value in body.items() if key != "runtime_versions"}
    hash_body["modes"] = {
        mode: {key: value for key, value in fields.items() if key != "average_latency_seconds"}
        for mode, fields in results.items()
    }
    body["receipt_sha256"] = _receipt_hash(hash_body)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"receipt_sha256": body["receipt_sha256"], "output": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
