"""NVIDIA NIM and deterministic request/response replay providers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def request_sha256(body: dict) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


class ReplayCacheMiss(FileNotFoundError):
    pass


class ReplayProvider:
    """Read only provider; cache files contain request and response bodies only."""
    def __init__(self, cache_dir: str | Path = "artifacts/llm_cache"):
        self.cache_dir = Path(cache_dir)

    def complete(self, request_body: dict) -> dict:
        key = request_sha256(request_body)
        path = self.cache_dir / f"{key}.json"
        if not path.is_file():
            raise ReplayCacheMiss(f"replay cache miss: {path}")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("request") != request_body or not isinstance(record.get("response"), dict):
            raise ValueError(f"invalid replay cache record: {path}")
        return record["response"]


class NvidiaNimProvider:
    """Small stdlib-only OpenAI-compatible NVIDIA NIM client with content-addressed cache."""
    def __init__(self, cache_dir: str | Path = "artifacts/llm_cache",
                 timeout: float = 90.0, base_url: str = NIM_BASE_URL, model: str = NIM_MODEL,
                 max_tokens: int = 1800):
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
        self.last_http_status: int | None = None
        self.last_latency_seconds: float | None = None

    def complete(self, request_body: dict) -> dict:
        # Caller supplies only evidence_packet and context_text; provider fixes the model settings.
        payload = dict(request_body)
        payload.update({"model": self.model, "temperature": 0, "max_tokens": self.max_tokens})
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
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        key = request_sha256(payload)
        cache_path = self.cache_dir / f"{key}.json"
        # Deliberately excludes credentials, headers and wall-clock values.
        cache_path.write_text(canonical_json({"request": payload, "response": response_body}) + "\n", encoding="utf-8")
        return response_body
