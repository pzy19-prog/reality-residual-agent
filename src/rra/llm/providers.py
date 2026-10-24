"""NVIDIA NIM and deterministic request/response replay providers."""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rra.llm.schema import PROPOSAL_SCHEMA

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"
_UNSET = object()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def request_sha256(body: dict) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def finalize_payload(request_body: dict, settings: Any) -> dict:
    """Apply provider settings so live and replay providers hash identical payloads."""
    def setting(name: str, default: Any) -> Any:
        return settings.get(name, default) if isinstance(settings, dict) else getattr(settings, name, default)

    payload = dict(request_body)
    model = setting("model", NIM_MODEL)
    max_tokens = setting("max_tokens", 1800)
    chat_template_kwargs = setting("chat_template_kwargs", {"enable_thinking": False})
    format_mode = setting("format_mode", "json_object")
    if format_mode not in ("json_object", "json_schema", "nvext_guided_json"):
        raise ValueError(f"unknown format_mode: {format_mode}")
    no_think = bool(setting("no_think", False))
    payload.update({"model": model, "temperature": 0, "max_tokens": int(max_tokens)})
    if format_mode == "json_object":
        payload["response_format"] = {"type": "json_object"}
        payload.pop("nvext", None)
    elif format_mode == "json_schema":
        payload.pop("nvext", None)
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "proposal", "schema": deepcopy(PROPOSAL_SCHEMA), "strict": True},
        }
    else:
        payload.pop("response_format", None)
        payload["nvext"] = {"guided_json": deepcopy(PROPOSAL_SCHEMA)}
    # Round numeric values embedded in JSON message content before cache hashing.
    for message in payload.get("messages", []):
        content = message.get("content")
        if not isinstance(content, str):
            continue
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            continue
        def rounded(value: Any) -> Any:
            if isinstance(value, float):
                return round(value, 6)
            if isinstance(value, list):
                return [rounded(item) for item in value]
            if isinstance(value, dict):
                return {key: rounded(item) for key, item in value.items()}
            return value
        message["content"] = canonical_json(rounded(parsed))
    if chat_template_kwargs is not None:
        payload["chat_template_kwargs"] = deepcopy(chat_template_kwargs)
    else:
        payload.pop("chat_template_kwargs", None)
    if no_think:
        payload["messages"] = deepcopy(payload["messages"])
        system_message = next((m for m in payload["messages"] if m.get("role") == "system"), None)
        if system_message is None:
            raise ValueError("no system message available for /no_think prefix")
        if not system_message["content"].startswith("/no_think\n"):
            system_message["content"] = "/no_think\n" + system_message["content"]
    return payload


class ReplayCacheMiss(FileNotFoundError):
    pass


class ReplayProvider:
    """Read only provider; cache files contain request and response bodies only."""
    def __init__(self, cache_dir: str | Path = "artifacts/llm_cache", *, model: str = NIM_MODEL,
                 max_tokens: int = 1800, chat_template_kwargs: dict | None = {"enable_thinking": False},
                 no_think: bool = False, format_mode: str = "json_object"):
        self.cache_dir = Path(cache_dir)
        self.settings = {"model": model, "max_tokens": max_tokens,
                         "chat_template_kwargs": chat_template_kwargs, "no_think": no_think,
                         "format_mode": format_mode}

    def complete(self, request_body: dict) -> dict:
        payload = finalize_payload(request_body, self.settings)
        key = request_sha256(payload)
        path = self.cache_dir / f"{key}.json"
        if not path.is_file():
            raise ReplayCacheMiss(f"replay cache miss: {path}")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("request") != payload or not isinstance(record.get("response"), dict):
            raise ValueError(f"invalid replay cache record: {path}")
        return record["response"]


class NvidiaNimProvider:
    """Small stdlib-only OpenAI-compatible NVIDIA NIM client with content-addressed cache."""
    def __init__(self, cache_dir: str | Path = "artifacts/llm_cache",
                 timeout: float = 90.0, base_url: str = NIM_BASE_URL, model: str = NIM_MODEL,
                 max_tokens: int = 1800, chat_template_kwargs: dict | None | object = _UNSET,
                 no_think: bool = False, format_mode: str = "json_object"):
        self.api_key = os.environ.get("NVIDIA_API_KEY")
        if not self.api_key:
            raise RuntimeError("NVIDIA_API_KEY is required")
        if max_tokens < 1500:
            raise ValueError("max_tokens must be at least 1500")
        self.cache_dir = Path(cache_dir)
        self.timeout = float(timeout)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = int(max_tokens)
        if chat_template_kwargs is _UNSET:
            chat_template_kwargs = {"enable_thinking": False}
        self.chat_template_kwargs = deepcopy(chat_template_kwargs)
        self.no_think = bool(no_think)
        self.format_mode = format_mode
        self.last_http_status: int | None = None
        self.last_latency_seconds: float | None = None
        self.last_response_body: dict | None = None
        self.last_request_body: dict | None = None

    def complete(self, request_body: dict) -> dict:
        # Caller supplies only evidence_packet and context_text; provider fixes the model settings.
        payload = finalize_payload(request_body, self)
        self.last_request_body = payload
        data = canonical_json(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions", data=data, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        import time
        started = time.monotonic()
        try:
            with urlopen(request, timeout=self.timeout) as response:
                self.last_http_status = response.status
                raw = response.read()
        except HTTPError as exc:
            self.last_http_status = exc.code
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"NVIDIA NIM HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"NVIDIA NIM request failed: {exc}") from exc
        finally:
            self.last_latency_seconds = time.monotonic() - started
        response_body = json.loads(raw.decode("utf-8"))
        self.last_response_body = response_body
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        key = request_sha256(payload)
        cache_path = self.cache_dir / f"{key}.json"
        # Deliberately excludes credentials, headers and wall-clock values.
        cache_path.write_text(canonical_json({"request": payload, "response": response_body}) + "\n", encoding="utf-8")
        return response_body
