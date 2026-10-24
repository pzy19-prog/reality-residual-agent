"""Schema-checked proposal adapter. The model selects structures only."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rra.llm.providers import ReplayCacheMiss
from rra.llm.providers import canonical_json, finalize_payload
from rra.s2.dsl import STRUCTURE_IDS, FaultHypothesis

FAULT_HYPOTHESIS_IDS = tuple(item.value for item in FaultHypothesis)

_ALLOWED_IDS = frozenset((*STRUCTURE_IDS, *FAULT_HYPOTHESIS_IDS))

SYSTEM_PROMPT = (
    "Propose an ordered list of hypotheses from the registered IDs only. "
    "Choose model structures only; do not estimate numeric parameters. "
    'Return an object matching this JSON schema exactly: '
    '{"items":[{"hypothesis_id":"SENSOR_BIAS","rationale":"…",'
    '"evidence_refs":["obs:0:1.200"]}]}. Each item requires hypothesis_id, '
    'rationale, and evidence_refs; no additional properties are allowed. '
    f"Allowed IDs: {', '.join((*STRUCTURE_IDS, *FAULT_HYPOTHESIS_IDS))}"
)


def proposal_request(evidence_packet: Any, s2_summary: Any = None) -> dict[str, Any]:
    user_body = {"evidence_packet": evidence_packet}
    if s2_summary is not None:
        user_body["s2_summary"] = s2_summary
    return {
        "temperature": 0,
        "max_tokens": 1800,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(
                user_body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            )},
        ],
    }


def request_template_sha256(settings: Any, request_body: dict[str, Any] | None = None) -> str:
    """Hash the finalized request skeleton with evidence replaced by fixed markers."""
    request = deepcopy(request_body) if request_body is not None else proposal_request(
        "<EVIDENCE_PACKET>", "<S2_SUMMARY>")
    if request_body is not None:
        for message in request.get("messages", []):
            if message.get("role") != "user" or not isinstance(message.get("content"), str):
                continue
            try:
                user = json.loads(message["content"])
            except json.JSONDecodeError:
                continue
            if "evidence_packet" in user:
                user["evidence_packet"] = "<EVIDENCE_PACKET>"
            if "s2_summary" in user:
                user["s2_summary"] = "<S2_SUMMARY>"
            message["content"] = json.dumps(user, sort_keys=True, separators=(",", ":"),
                                             ensure_ascii=False)
    payload = finalize_payload(request, settings)
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class ProposalItem(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    hypothesis_id: str
    rationale: str = Field(min_length=1)
    evidence_refs: list[str]


class Proposal(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    items: list[ProposalItem] = Field(default_factory=list)
    error: str | None = None
    receipt: dict[str, Any] = Field(default_factory=dict)


class Provider(Protocol):
    def complete(self, request_body: dict) -> dict: ...


_NUMERIC = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def _extract_content(response: Any) -> Any:
    if isinstance(response, str):
        return response
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return response


def _find_numeric_parameters(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                found.append(next_path)
            else:
                found.extend(_find_numeric_parameters(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_find_numeric_parameters(item, f"{path}[{index}]"))
    return found


class HypothesisProposer:
    def __init__(self, provider: Provider):
        self.provider = provider

    def propose(self, evidence_packet: dict, context_text: str = "", *,
                s2_summary: dict | None = None) -> Proposal:
        request_body = proposal_request(evidence_packet, s2_summary)
        receipt: dict[str, Any] = {"unknown_ids": [], "ignored_numeric_parameters": []}
        try:
            response = self.provider.complete(request_body)
            content = _extract_content(response)
            if not isinstance(content, (str, dict)):
                raise ValueError("provider returned no JSON content")
            parsed = json.loads(content) if isinstance(content, str) else content
            if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
                raise ValueError("response must be a JSON object with an items list")
            receipt["ignored_numeric_parameters"] = _find_numeric_parameters(parsed)
            valid_items: list[ProposalItem] = []
            # Validate the overall envelope; then drop unknown IDs item-wise.
            for index, raw_item in enumerate(parsed["items"]):
                if not isinstance(raw_item, dict):
                    raise ValueError(f"item {index} must be an object")
                item = ProposalItem.model_validate(raw_item)
                if item.hypothesis_id not in _ALLOWED_IDS:
                    receipt["unknown_ids"].append(item.hypothesis_id)
                    continue
                if _NUMERIC.search(item.rationale):
                    receipt["ignored_numeric_parameters"].append(f"$.items[{index}].rationale")
                    item.rationale = _NUMERIC.sub("[numeric value omitted]", item.rationale)
                valid_items.append(item)
            return Proposal(items=valid_items, receipt=receipt)
        except ReplayCacheMiss:
            raise
        except (ValueError, TypeError, json.JSONDecodeError, ValidationError, RuntimeError, OSError) as exc:
            return Proposal(items=[], error=f"{type(exc).__name__}: {exc}", receipt=receipt)
