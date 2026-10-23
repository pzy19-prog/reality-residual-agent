"""Minimal stdlib REST client for the Zetaris SQL editor endpoint."""
from __future__ import annotations

import json
import os
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class ZetarisError(RuntimeError):
    pass


class ZetarisClient:
    def __init__(self, base_url: str = "http://localhost:8888/api/v1.0", org_id: str = "1"):
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id
        self.token = os.environ.get("ZETARIS_TOKEN", "")
        if not self.token:
            raise ZetarisError("ZETARIS_TOKEN is required")

    def query(self, sql: str, limit: int = 5000) -> dict:
        body = json.dumps({"queryId": str(uuid.uuid4()), "sql": sql,
                           "source": "SqlEditor", "limit": limit}).encode()
        req = Request(self.base_url + "/sql-editor/sqls/run", data=body, method="POST", headers={
            "Authorization": "Bearer " + self.token, "X-Org-ID": self.org_id,
            "X-Request-ID": str(uuid.uuid4()), "Content-Type": "application/json",
        })
        try:
            with urlopen(req, timeout=120) as response:
                payload = json.loads(response.read())
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:600]
            detail = detail.replace(self.token, "[REDACTED]")
            raise ZetarisError(f"Zetaris HTTP {exc.code}: {detail}") from None
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ZetarisError(f"Zetaris request failed: {type(exc).__name__}") from None
        if not isinstance(payload, dict):
            raise ZetarisError("Zetaris returned non-object JSON")
        return payload

    @staticmethod
    def rows(payload: dict) -> list:
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise ZetarisError("Zetaris response has no row array")
        return data
