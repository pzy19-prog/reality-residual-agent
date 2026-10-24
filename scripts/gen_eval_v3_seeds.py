#!/usr/bin/env python3
"""Generate the frozen eval-v3 seed file after the implementation is tagged."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path


LOW, HIGH, COUNT = 10_000, 2_147_483_647, 100


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def generate(root: Path, freeze_tag: str) -> tuple[int, str]:
    root = root.resolve()
    target = root / "config" / "eval_seeds_v3.json"
    if not freeze_tag or any(ch.isspace() for ch in freeze_tag):
        raise ValueError("invalid freeze tag")
    try:
        tagged_commit = _git(root, "rev-parse", "--verify", f"{freeze_tag}^{{commit}}")
        head = _git(root, "rev-parse", "HEAD")
        status = _git(root, "status", "--porcelain", "--untracked-files=all")
    except (OSError, subprocess.CalledProcessError):
        raise ValueError("freeze tag or git repository validation failed") from None
    if head != tagged_commit:
        raise ValueError("HEAD does not match freeze tag")
    if status:
        raise ValueError("working tree is not clean")
    if target.exists():
        raise ValueError("seed file already exists")

    seeds = secrets.SystemRandom().sample(range(LOW, HIGH), COUNT)
    payload = {
        "schema_version": "rra.eval-seeds.v3",
        "role": "eval_v3",
        "count": COUNT,
        "range": [LOW, HIGH],
        "generator": "secrets.SystemRandom().sample",
        "freeze_tag": freeze_tag,
        "freeze_commit": tagged_commit,
        "seeds": seeds,
    }
    encoded = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return COUNT, hashlib.sha256(encoded).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-tag", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        count, digest = generate(args.root, args.freeze_tag)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=__import__("sys").stderr)
        return 2
    print(f"count={count} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
