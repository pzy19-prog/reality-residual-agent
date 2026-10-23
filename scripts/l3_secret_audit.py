#!/usr/bin/env python3
"""Scan worktree outputs and delivery report for the in-memory pass token."""
import os
import subprocess
from pathlib import Path

token = os.environ.get("ZETARIS_TOKEN", "").encode()
if not token:
    raise SystemExit("missing token environment")
root = Path(__file__).resolve().parents[1]
files = [p for p in root.rglob("*") if p.is_file() and not any(
    part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in p.parts)]
files.append(Path.home() / "reality-residual-agent-worktrees/_reports/REPORT_D2_L3.md")
hits = []
for path in files:
    try:
        if path.is_file() and token in path.read_bytes():
            hits.append(str(path))
    except (OSError, ValueError):
        pass
print(f"token_match_files={len(hits)}")
for path in hits:
    print(f"MATCH {path}")
if hits:
    raise SystemExit(1)
