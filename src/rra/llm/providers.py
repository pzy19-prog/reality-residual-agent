"""NVIDIA NIM and deterministic request/response replay providers."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rra.llm.schema import PROPOSAL_SCHEMA

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"
DEFAULT_FORMAT_MODE = "json_object"
LIVE_ATTEMPTS = 5
RETRY_AFTER_CAP_SECONDS = 60.0
OUTAGE_LIMIT = 10
_UNSET = object()
_AUTH_STATUS = frozenset({401, 403})
_TRANSIENT_STATUS = frozenset({408, 429})


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
    format_mode = setting("format_mode", DEFAULT_FORMAT_MODE)
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


class CachedProviderError(RuntimeError):
    """Final cached provider failure. The message is the error class, not a body."""


class LiveDeadlineExceeded(Exception):
    """A new HTTP attempt would start at or after the live-fill deadline."""


class LiveOutageStop(Exception):
    """Ten consecutive live requests ended in cached error records."""


class _DeterministicHTTP(Exception):
    def __init__(self, status: int):
        self.status = status


class _TransientHTTP(Exception):
    def __init__(self, status: int | None, headers: Any = None):
        self.status = status
        self.headers = headers


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_live_deadline: datetime | None = None
_outage_lock = threading.Lock()
_outage_streak = 0
_outage_enabled = False


def set_live_deadline(deadline: datetime | None) -> None:
    global _live_deadline
    _live_deadline = deadline


def live_deadline_reached() -> bool:
    deadline = _live_deadline
    return deadline is not None and utc_now() >= deadline


def reset_live_outage() -> None:
    global _outage_streak, _outage_enabled
    with _outage_lock:
        _outage_streak = 0
        _outage_enabled = True


def disable_live_outage() -> None:
    global _outage_enabled
    with _outage_lock:
        _outage_enabled = False


def note_live_success() -> None:
    global _outage_streak
    with _outage_lock:
        if _outage_enabled:
            _outage_streak = 0


def note_live_error_record() -> None:
    global _outage_streak
    with _outage_lock:
        if not _outage_enabled:
            return
        _outage_streak += 1
        if _outage_streak >= OUTAGE_LIMIT:
            raise LiveOutageStop("ten consecutive live requests ended in error records")


def _status_kind(status: int) -> str:
    if status in _AUTH_STATUS:
        return "auth"
    if status in _TRANSIENT_STATUS or status >= 500:
        return "transient"
    return "deterministic"


def _retry_after_seconds(headers: Any) -> float | None:
    if headers is None or not hasattr(headers, "get"):
        return None
    raw = headers.get("Retry-After")
    if raw is None:
        return None
    text = str(raw).strip()
    try:
        return float(text)
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (when - utc_now()).total_seconds()


def _backoff_seconds(attempt: int, headers: Any) -> float:
    retry_after = _retry_after_seconds(headers)
    delay = float(2 ** (attempt - 1)) if retry_after is None else retry_after
    return min(RETRY_AFTER_CAP_SECONDS, max(0.0, delay))


def _write_new_cache(path: Path, record: dict) -> None:
    """Create a cache file. An existing file is left untouched."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (canonical_json(record) + "\n").encode("utf-8")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


class ReplayProvider:
    """Read only provider; cache files contain request and response bodies only."""
    def __init__(self, cache_dir: str | Path = "artifacts/llm_cache", *, model: str = NIM_MODEL,
                 max_tokens: int = 1800, chat_template_kwargs: dict | None = {"enable_thinking": False},
                 no_think: bool = False, format_mode: str = DEFAULT_FORMAT_MODE):
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
        if record.get("request") != payload:
            raise ValueError(f"invalid replay cache record: {path}")
        error = record.get("error")
        if isinstance(error, dict) and "response" not in record:
            kind = error.get("class")
            if kind not in ("deterministic", "transient_exhausted"):
                raise ValueError(f"invalid replay cache record: {path}")
            raise CachedProviderError(str(kind))
        if not isinstance(record.get("response"), dict):
            raise ValueError(f"invalid replay cache record: {path}")
        return record["response"]


class NvidiaNimProvider:
    """Small stdlib-only OpenAI-compatible NVIDIA NIM client with content-addressed cache."""
    def __init__(self, cache_dir: str | Path = "artifacts/llm_cache",
                 timeout: float = 90.0, base_url: str = NIM_BASE_URL, model: str = NIM_MODEL,
                 max_tokens: int = 1800, chat_template_kwargs: dict | None | object = _UNSET,
                 no_think: bool = False, format_mode: str = DEFAULT_FORMAT_MODE):
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

    def _cache_error(self, payload: dict, status: int | None, kind: str) -> None:
        key = request_sha256(payload)
        # Error records keep the status and class only: no body, credential, or time.
        _write_new_cache(self.cache_dir / f"{key}.json", {
            "request": payload,
            "error": {"http_status": status, "class": kind},
        })
        note_live_error_record()

    def _one_attempt(self, data: bytes) -> dict:
        request = Request(
            f"{self.base_url}/chat/completions", data=data, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        started = time.monotonic()
        try:
            with urlopen(request, timeout=self.timeout) as response:
                self.last_http_status = response.status
                raw = response.read()
                headers = getattr(response, "headers", None)
                status = response.status
        except HTTPError as exc:
            self.last_http_status = exc.code
            exc.read()
            if _status_kind(exc.code) == "auth":
                raise SystemExit(f"NVIDIA NIM HTTP {exc.code}; stop Phase B") from None
            if _status_kind(exc.code) == "deterministic":
                raise _DeterministicHTTP(exc.code) from None
            raise _TransientHTTP(exc.code, exc.headers) from None
        except (URLError, TimeoutError) as exc:
            self.last_http_status = None
            raise _TransientHTTP(None) from exc
        finally:
            self.last_latency_seconds = time.monotonic() - started
        try:
            response_body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _TransientHTTP(status, headers) from exc
        if not isinstance(response_body, dict):
            raise _TransientHTTP(status, headers)
        return response_body

    def complete(self, request_body: dict) -> dict:
        # Caller supplies only evidence_packet and context_text; provider fixes the model settings.
        payload = finalize_payload(request_body, self)
        self.last_request_body = payload
        data = canonical_json(payload).encode("utf-8")
        last_status: int | None = None
        for attempt in range(1, LIVE_ATTEMPTS + 1):
            if live_deadline_reached():
                raise LiveDeadlineExceeded("live fill deadline reached")
            try:
                response_body = self._one_attempt(data)
            except _DeterministicHTTP as exc:
                self._cache_error(payload, exc.status, "deterministic")
                raise CachedProviderError("deterministic") from None
            except _TransientHTTP as exc:
                last_status = exc.status
                if attempt == LIVE_ATTEMPTS:
                    self._cache_error(payload, last_status, "transient_exhausted")
                    raise CachedProviderError("transient_exhausted") from None
                time.sleep(_backoff_seconds(attempt, exc.headers))
                continue
            self.last_response_body = response_body
            key = request_sha256(payload)
            _write_new_cache(self.cache_dir / f"{key}.json",
                             {"request": payload, "response": response_body})
            note_live_success()
            return response_body
        raise CachedProviderError("transient_exhausted")
