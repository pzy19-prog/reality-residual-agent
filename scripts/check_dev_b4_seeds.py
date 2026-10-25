#!/usr/bin/env python3
"""Check that a development B4 artifact uses only the registered diag subset."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIAG_PATH = "artifacts/s2/diag-d1g.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def check_artifact(artifact: dict[str, Any], diag_seeds: set[int]) -> list[str]:
    errors: list[str] = []
    identity = artifact.get("seed_identity")
    if not isinstance(identity, dict) or identity.get("path") != DIAG_PATH:
        errors.append(f"seed_identity.path must be {DIAG_PATH!r}")
    else:
        identity_values = identity.get("values")
        if (not isinstance(identity_values, list)
                or any(not isinstance(seed, int) for seed in identity_values)
                or set(identity_values) != diag_seeds):
            errors.append("seed_identity.values must match diag-d1g.json seeds")

    episodes = artifact.get("episodes")
    if not isinstance(episodes, list):
        errors.append("episodes must be a list")
        episodes = []
    episode_seeds: set[int] = set()
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict) or not isinstance(episode.get("seed"), int):
            errors.append(f"episodes[{index}].seed must be an integer")
            continue
        episode_seeds.add(episode["seed"])

    outside = episode_seeds - diag_seeds
    if outside:
        errors.append(f"episode seeds outside diag subset: {sorted(outside)}")
    excluded = sorted(seed for seed in episode_seeds if seed % 19 == 9)
    if excluded:
        errors.append(f"episode seeds include excluded seed % 19 == 9: {excluded}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("b4_dev_json", type=Path)
    args = parser.parse_args(argv)
    try:
        artifact = _load(args.b4_dev_json)
        diag = _load(ROOT / DIAG_PATH)
        raw_seeds = diag.get("seeds")
        if not isinstance(raw_seeds, list) or any(not isinstance(seed, int) for seed in raw_seeds):
            raise ValueError(f"{DIAG_PATH}: seeds must be an integer list")
        errors = check_artifact(artifact, set(raw_seeds))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"seed check failed: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("seed check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"seed check passed: {args.b4_dev_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
