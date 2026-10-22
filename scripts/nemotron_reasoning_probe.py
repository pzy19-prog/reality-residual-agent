"""Probe registered Nemotron thinking controls, one live request per mode, no retries."""
from __future__ import annotations

import json
import os
import re

from rra.eval.context_v3 import STRUCTURE_IDS
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import NvidiaNimProvider, request_sha256

PACKET = {
    "observations": [
        {"target_id": "synthetic-1", "step": 4, "time": 0.4,
         "observed_x": 0.438, "nominal_x": 0.400},
        {"target_id": "synthetic-1", "step": 5, "time": 0.5,
         "observed_x": 0.552, "nominal_x": 0.500},
        {"target_id": "synthetic-1", "step": 6, "time": 0.6,
         "observed_x": 0.671, "nominal_x": 0.600},
    ],
    "command_feedback": [],
    "known_configuration": {"dt": 0.1, "belt_speed": 1.0},
}
CONTEXT = "The position sensor was calibrated recently, though its stability should be checked."
MODES = (
    ("a", {"chat_template_kwargs": {"enable_thinking": False}}),
    ("b", {"chat_template_kwargs": None, "no_think": True}),
    ("c", {"chat_template_kwargs": {"enable_thinking": False}, "no_think": True}),
)


def _redact(text: str, key: str) -> str:
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)


def _response_metadata(response: dict | None) -> tuple[str | None, int | None, bool]:
    if not response:
        return None, None, False
    choice = (response.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    usage = response.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    reasoning_tokens = details.get("reasoning_tokens", usage.get("reasoning_tokens"))
    content = message.get("content")
    if not isinstance(content, str):
        return choice.get("finish_reason"), reasoning_tokens, False
    try:
        parsed = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return choice.get("finish_reason"), reasoning_tokens, False
    return choice.get("finish_reason"), reasoning_tokens, isinstance(parsed, dict)


def main() -> int:
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    results: list[dict] = []
    for label, settings in MODES:
        provider = NvidiaNimProvider(**settings)
        proposal = HypothesisProposer(provider).propose(PACKET, CONTEXT)
        response = provider.last_response_body
        finish_reason, reasoning_tokens, valid_json = _response_metadata(response)
        ids = [item.hypothesis_id for item in proposal.items if item.hypothesis_id in STRUCTURE_IDS]
        cache_file = None
        if provider.last_request_body is not None:
            cache_file = f"artifacts/llm_cache/{request_sha256(provider.last_request_body)}.json"
        result = {
            "mode": label,
            "http_status": provider.last_http_status,
            "finish_reason": finish_reason,
            "reasoning_tokens": reasoning_tokens,
            "content_valid_json": valid_json,
            "structure_ids": ids,
            "latency_seconds": provider.last_latency_seconds,
            "response_model": response.get("model") if response else None,
            "cache_file": cache_file,
            "error": _redact(proposal.error, api_key) if proposal.error else None,
        }
        results.append(result)
        print(json.dumps(result, sort_keys=True))
        if valid_json and ids and finish_reason == "stop":
            break
        if provider.last_http_status in (401, 403):
            break
    return 0 if any(r["content_valid_json"] and r["structure_ids"] and r["finish_reason"] == "stop" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
