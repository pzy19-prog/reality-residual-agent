"""Frozen eval-v3 seed loading, baseline runners, and receipt generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

from rra.runtime import runtime_versions

ROOT = Path(__file__).resolve().parents[3]
ROWS = ("b1b3", "b2", "b1-legacy", "b4")
SEED_SCHEMA = "rra.eval-seeds.v3"
# Addendum 06 §3.3, owner patch P-1: distinct live requests on one eval-v3 run.
DEFAULT_MAX_LIVE_CALLS = 2500
DEV_SEEDS_PATH = ROOT / "config" / "dev_seeds.json"
DIAG_SUBSET_PATH = ROOT / "artifacts" / "s2" / "diag-d1g.json"


class LiveBudgetExceeded(Exception):
    """Raised before a new distinct live request would pass the run cap."""


def _canonical_sha(value: dict[str, Any]) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()


def _ledger_shas(path: Path) -> list[str]:
    """Distinct request hashes in ledger order. The file is never rewritten."""
    if not path.is_file():
        return []
    found: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        sha = item.get("request_sha256") if isinstance(item, dict) else None
        if isinstance(sha, str) and sha not in seen:
            seen.add(sha)
            found.append(sha)
    return found


def _append_ledger(path: Path, sha: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"request_sha256": sha}, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


class _LiveBudget:
    """Count distinct finalized request payloads and completed B4 text conditions.

    `already` is the number of distinct live requests already recorded. For an
    eval-v3 live run that record is the append-only ledger. Cache hits are not
    reserved, so a rerun spends the remaining cap only on requests that still miss.
    """

    def __init__(self, limit: int, already: int = 0, seen: set[str] | None = None,
                 ledger_path: Path | None = None):
        self.limit = limit
        self.already = already
        self.seen = set(seen or ())
        self.ledger_path = ledger_path
        self.keys: set[str] = set()
        self.completed_pairs = 0
        self._lock = threading.Lock()
        self._local = threading.local()

    def reserve(self, key: str) -> None:
        with self._lock:
            if key in self.seen or key in self.keys:
                return
            if self.already + len(self.keys) >= self.limit:
                raise LiveBudgetExceeded("maximum distinct live request count reached")
            if self.ledger_path is not None:
                _append_ledger(self.ledger_path, key)
            self.keys.add(key)

    def distinct_total(self) -> int:
        return self.already + len(self.keys)

    def note_episode(self, variant: str | None) -> None:
        if variant == "B4_STRICT":
            self._local.pending_strict = True
            return
        if variant == "B4_TIEBREAK" and getattr(self._local, "pending_strict", False):
            self._local.pending_strict = False
            with self._lock:
                self.completed_pairs += 1


class _LiveBudgetScope:
    def __init__(self, limit: int, already: int = 0, seen: set[str] | None = None,
                 ledger_path: Path | None = None):
        self.budget = _LiveBudget(limit, already, seen, ledger_path)
        self._provider = None
        self._episode = None

    def __enter__(self) -> _LiveBudget:
        from rra.eval import b4_dev
        from rra.llm.providers import finalize_payload, request_sha256

        budget = self.budget
        original_provider = b4_dev.NvidiaNimProvider
        original_episode = b4_dev.run_episode

        class LimitedProvider(original_provider):
            def complete(self, request_body: dict) -> dict:
                payload = finalize_payload(request_body, self)
                budget.reserve(request_sha256(payload))
                return super().complete(request_body)

        def wrapped_episode(*args: Any, **kwargs: Any) -> dict:
            result = original_episode(*args, **kwargs)
            budget.note_episode(kwargs.get("s2_variant"))
            return result

        b4_dev.NvidiaNimProvider = LimitedProvider
        b4_dev.run_episode = wrapped_episode
        self._provider = original_provider
        self._episode = original_episode
        return budget

    def __exit__(self, exc_type, exc, tb) -> bool:
        from rra.eval import b4_dev

        if self._provider is not None:
            b4_dev.NvidiaNimProvider = self._provider
        if self._episode is not None:
            b4_dev.run_episode = self._episode
        return False


_EVAL_ALLOW_FILE = "config/eval_seeds_v3.json"
_EVAL_ALLOW_PREFIXES = ("artifacts/eval_v3/", "artifacts/llm_cache/")
_CACHE_PREFIX = "artifacts/llm_cache/"


def _allowed_eval_path(path: str) -> bool:
    return path == _EVAL_ALLOW_FILE or path.startswith(_EVAL_ALLOW_PREFIXES)


def _name_status_rows(text: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((parts[0], parts[1:]))
    return rows


def _reject_disallowed(status: str, paths: list[str]) -> None:
    for path in paths:
        if not _allowed_eval_path(path):
            raise ValueError("changes since freeze tag include a path outside the eval allowlist")
    if any(path.startswith(_CACHE_PREFIX) for path in paths) and status != "A":
        raise ValueError("existing llm cache files may only be added")


def _validate_eval_guard(root: Path, freeze_tag: str) -> None:
    """Allow only seed, eval artifact, and new cache paths after the freeze tag.

    Tracked history, tracked worktree edits, and untracked files all use that
    allowlist. Cache paths may be added, never modified, deleted, or renamed.
    """
    if not freeze_tag:
        raise ValueError("--freeze-tag is required for eval_v3")
    try:
        committed = _git(root, "diff", "--name-status", "--find-renames", freeze_tag, "HEAD")
        tracked = _git(root, "diff", "--name-status", "--find-renames", "HEAD")
        status = _git(root, "status", "--porcelain", "--untracked-files=all")
    except (OSError, subprocess.CalledProcessError):
        raise ValueError("eval freeze tag validation failed") from None
    for row_status, paths in _name_status_rows(committed):
        _reject_disallowed(row_status, paths)
    for row_status, paths in _name_status_rows(tracked):
        _reject_disallowed(row_status, paths)
    for line in status.splitlines():
        if not line.startswith("??"):
            continue
        path = line[3:]
        if not _allowed_eval_path(path):
            raise ValueError("changes since freeze tag include a path outside the eval allowlist")


def load_seed_file(path: Path, role: str, *, freeze_tag: str | None = None,
                   root: Path = ROOT) -> tuple[list[int], str]:
    if role not in ("dev", "eval_v3"):
        raise ValueError("role must be dev or eval_v3")
    if role == "eval_v3":
        _validate_eval_guard(root, freeze_tag or "")
        expected = root / "config" / "eval_seeds_v3.json"
        if path.resolve() != expected.resolve():
            raise ValueError("eval_v3 seeds must come from config/eval_seeds_v3.json")
    elif path is None:
        raise ValueError("--seeds-file is required for role dev")
    try:
        raw_bytes = path.read_bytes()
        data = json.loads(raw_bytes)
    except (OSError, json.JSONDecodeError):
        raise ValueError("seed file could not be read") from None
    if not isinstance(data, dict) or not isinstance(data.get("seeds"), list):
        raise ValueError("seed file has an invalid schema")
    seeds = data["seeds"]
    if any(type(seed) is not int for seed in seeds):
        raise ValueError("seed file must contain integer seeds")
    if len(seeds) != len(set(seeds)):
        raise ValueError("seed file contains duplicate seeds")
    if role == "eval_v3":
        if (data.get("schema_version") != SEED_SCHEMA or data.get("role") != "eval_v3"
                or data.get("count") != 100 or len(seeds) != 100
                or data.get("range") != [10_000, 2_147_483_647]
                or any(not 10_000 <= seed < 2_147_483_647 for seed in seeds)):
            raise ValueError("eval_v3 seed file failed frozen schema validation")
        if data.get("freeze_tag") != freeze_tag:
            raise ValueError("seed file freeze tag does not match --freeze-tag")
        try:
            tagged_commit = _git(root, "rev-parse", "--verify", f"{freeze_tag}^{{commit}}")
        except (OSError, subprocess.CalledProcessError):
            raise ValueError("eval freeze tag validation failed") from None
        if data.get("freeze_commit") != tagged_commit:
            raise ValueError("seed file freeze commit does not match its tag")
    return seeds, hashlib.sha256(raw_bytes).hexdigest()


def _case(index: int, seed: int):
    from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode

    structures = composition_structures()
    case = index % 19
    return (realize_episode(seed, structures[case]) if case < len(structures)
            else realize_episode(seed, (), FAULT_FAMILIES[case - len(structures)]))


def _case_counts(seeds: list[int], indices: list[int] | None = None) -> dict[str, int]:
    used = list(range(len(seeds))) if indices is None else indices
    if len(used) != len(seeds):
        raise ValueError("seed and index lists differ in length")
    return {str(case): sum(index % 19 == case for index in used) for case in range(19)}


def _same_file(path: Path, canonical: Path) -> bool:
    try:
        return path.resolve() == canonical.resolve()
    except OSError:
        return False


def _run_b1b3(seeds_path: Path, output_dir: Path, nproc: int | None) -> tuple[dict[str, Any], dict[str, Any]]:
    from rra.eval.b3_dev import run_b3_dev

    # The canonical dev file keeps the historical path string, so the dev receipt
    # stays byte-identical to s2-b3-dev. Any other file is recorded as given.
    recorded = None if _same_file(seeds_path, DEV_SEEDS_PATH) else seeds_path
    with tempfile.TemporaryDirectory(prefix="eval-v3-b1b3-") as temporary:
        dev_receipt = run_b3_dev(Path(temporary), nproc=nproc, seeds_path=recorded)
    episodes = dev_receipt["episodes"]
    return ({"metrics": dev_receipt["metrics"], "episodes": episodes,
             "episode_count": dev_receipt["episode_count"],
             "b1": "corrected", "b3": "exhaustive-14-structures"},
            {"runtime_versions": dev_receipt.get("runtime_versions", runtime_versions())})


def _run_b2(seeds: list[int]) -> dict[str, Any]:
    from rra.eval.framework import v3_world_config
    from rra.eval.runner import score_against_b1_denominators
    from rra.evidence import run_episode

    config = v3_world_config("nominal")
    selected = json.loads((ROOT / "artifacts/h1/b2-grid.json").read_text())["selected"]
    t_value, r_value = float(selected["T"]), float(selected["R"])
    rows = []
    for index, seed in enumerate(seeds):
        realization = _case(index, seed)
        b1 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization)
        b2 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                         fast_time_limit=t_value, fast_residual_threshold=r_value)
        score = score_against_b1_denominators(b2, realization, config, b1)
        rows.append({"seed": seed, "case": index % 19, "b1_receipt_sha256": b1["receipt_sha256"],
                     "b2_receipt_sha256": b2["receipt_sha256"], "score": score})
    def total(key: str) -> int:
        return sum(int(row["score"][key]) for row in rows)
    challenge_count = total("recoverable_challenge_count")
    preservation_count = total("preservation_count")
    metrics = {
        "episodes": len(rows),
        "recoverable_success": total("challenge_success_count") / challenge_count if challenge_count else 0.0,
        "challenge_success_count": total("challenge_success_count"),
        "recoverable_challenge_count": challenge_count,
        "wrong_disposition": total("wrong_disposition_count"),
        "miss": total("ordinary_miss_count"),
        "unsafe_action": total("unsafe_action_count"),
        "preservation_regression_count": total("preservation_regression_count"),
        "preservation_count": preservation_count,
    }
    return {"metrics": metrics, "episodes": rows,
            "parameters": {"T": t_value, "R": r_value},
            "b2_grid_receipt_sha256": json.loads(
                (ROOT / "artifacts/h1/b2-grid.json").read_text())["receipt_sha256"]}


def _run_b1_legacy(seeds: list[int]) -> dict[str, Any]:
    from rra.eval.dev_diagnostics import run_b1_diagnostic

    diagnostic = run_b1_diagnostic("legacy", seeds)
    return {"metrics": {"scenario_count": len(diagnostic["rows"]),
                         "episode_count": len(seeds) * len(diagnostic["rows"])},
            "episodes": diagnostic["rows"], "comparison_basis":
            "Fourteen scenarios from config/scenarios.json, aggregated over the supplied seed list. artifacts/h1/b1-legacy-dev.json stores those scenario rows, not per-seed receipts; compare scenario, success, coverage, precision, mae, terminal_counts, and escalations.",
            "diagnostic": diagnostic}


def _estimate_seed_requests(task: tuple[int, int]) -> set[str]:
    """Return finalized-request hashes for one seed under an empty proposal."""
    from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
    from rra.eval.framework import v3_world_config
    from rra.evidence import run_episode
    from rra.llm.adapter import HypothesisProposer
    from rra.llm.providers import NIM_MODEL, finalize_payload, request_sha256

    index, seed = task
    realization = _case(index, seed)
    contexts = freeze_episode_contexts(
        str(seed), seed, realization.fault_family or realization.structure)
    requests: set[str] = set()
    settings = {"model": NIM_MODEL, "max_tokens": 1800,
                "chat_template_kwargs": {"enable_thinking": False}, "no_think": False}

    class _RecordingProvider:
        last_http_status = None

        def complete(self, request_body: dict) -> dict:
            requests.add(request_sha256(finalize_payload(request_body, settings)))
            return {"choices": [{"message": {"content": "{\"items\": []}"}}]}

    config = v3_world_config("nominal")
    proposer = HypothesisProposer(_RecordingProvider())
    for variant in VARIANTS:
        context = contexts[variant]
        # An empty proposal does not select a structure, so B4-strict and
        # B4-tiebreak keep the same action and the same later requests.
        # Counting strict once is the deduplicated request set of the paired run.
        run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                    text_context=context.text, system2_enabled=True, s2_variant="B4_STRICT",
                    proposer=proposer)
    return requests


def _prior_distinct_live_requests(output_dir: Path) -> int:
    """Read the live-request total already written for this output directory."""
    path = output_dir / "b4.json"
    if not path.is_file():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    value = data.get("distinct_live_requests", 0) if isinstance(data, dict) else 0
    if type(value) is not int or value < 0:
        return 0
    return value


def _run_b4(seeds_path: Path, output_dir: Path, *, replay: bool, live: bool,
            subset: bool, max_live_calls: int, nproc: int | None,
            role: str = "dev") -> dict[str, Any]:
    from rra.eval import b4_dev

    # subset=True reads the registered diag file and keeps each seed's dev index.
    # The canonical dev file likewise keeps the historical path string.
    recorded = None if subset or _same_file(seeds_path, DEV_SEEDS_PATH) else seeds_path
    if not live:
        result = b4_dev.run_b4_dev(output_dir, nproc=nproc, subset=subset, replay_only=replay,
                                   seeds_path=recorded)
        return {"status": "complete", "metrics": result["metrics"],
                "episodes": result["episodes"], "llm_calls": result["llm_calls"],
                "subset": subset, "max_live_calls": max_live_calls,
                "distinct_live_requests": 0}
    # eval-v3 counts from the append-only ledger. Dev keeps the prior receipt total.
    ledger_path = output_dir / "live_ledger.jsonl" if role == "eval_v3" else None
    if ledger_path is not None:
        seen = set(_ledger_shas(ledger_path))
        already = len(seen)
    else:
        seen = set()
        already = _prior_distinct_live_requests(output_dir)
    with _LiveBudgetScope(max_live_calls, already, seen, ledger_path) as budget:
        try:
            result = b4_dev.run_b4_dev(output_dir, nproc=nproc, subset=subset,
                                       replay_only=False, seeds_path=recorded)
        except LiveBudgetExceeded:
            return {"status": "incomplete", "reason": "max_live_calls_reached",
                    "max_live_calls": max_live_calls,
                    "distinct_live_requests": budget.distinct_total(),
                    "completed_text_condition_pairs": budget.completed_pairs}
    return {"status": "complete", "metrics": result["metrics"],
            "episodes": result["episodes"], "llm_calls": result["llm_calls"],
            "subset": subset, "max_live_calls": max_live_calls,
            "distinct_live_requests": budget.distinct_total()}


def estimate_b4(seeds: list[int], indices: list[int] | None = None) -> int:
    """Count unique finalized requests recorded by an empty-proposal provider."""
    if indices is None:
        indices = list(range(len(seeds)))
    if len(indices) != len(seeds):
        raise ValueError("seed and index lists differ in length")
    tasks = list(zip(indices, seeds))
    workers = min(8, os.cpu_count() or 1, max(1, len(tasks)))
    if workers == 1:
        per_seed = map(_estimate_seed_requests, tasks)
        fingerprints = set().union(*per_seed)
    else:
        with mp.Pool(processes=workers) as pool:
            per_seed = pool.map(_estimate_seed_requests, tasks)
        fingerprints = set().union(*per_seed)
    return len(fingerprints)


def run_row(row: str, *, seeds: list[int], seed_path: Path, seed_sha256: str,
            output_dir: Path, role: str, nproc: int | None = None, replay: bool = False,
            live: bool = False, subset: bool = False,
            max_live_calls: int = DEFAULT_MAX_LIVE_CALLS,
            indices: list[int] | None = None) -> dict[str, Any]:
    if row == "b1b3":
        result, auxiliary = _run_b1b3(seed_path, output_dir, nproc)
    elif row == "b2":
        result, auxiliary = _run_b2(seeds), {}
    elif row == "b1-legacy":
        result, auxiliary = _run_b1_legacy(seeds), {}
    elif row == "b4":
        result, auxiliary = _run_b4(seed_path, output_dir, replay=replay, live=live,
                                    subset=subset, max_live_calls=max_live_calls,
                                    nproc=nproc, role=role), {}
    else:
        raise ValueError(f"unknown row: {row}")
    receipt: dict[str, Any] = {
        "schema_version": "rra.eval-v3.row.v1", "row": row, "role": role,
        "seed_file_sha256": seed_sha256, "seed_count": len(seeds),
        "case_episode_counts": _case_counts(seeds, indices),
        "status": result.get("status", "complete"),
        **result, "runtime_versions": auxiliary.get("runtime_versions", runtime_versions()),
        "git_sha": _git(ROOT, "rev-parse", "HEAD"),
    }
    receipt["receipt_sha256"] = _canonical_sha({
        key: value for key, value in receipt.items()
        if key not in ("runtime_versions", "git_sha", "receipt_sha256")
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{row}.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    metrics = receipt.get("metrics", {})
    lines = [f"# eval-v3 {row}", "", f"Status: {receipt['status']}"]
    if receipt["status"] != "complete":
        lines.append(f"Reason: {receipt.get('reason', '')}")
        if "completed_text_condition_pairs" in receipt:
            lines.append(
                f"Completed text-condition pairs: {receipt['completed_text_condition_pairs']}")
        if "distinct_live_requests" in receipt:
            lines.append(f"Distinct live requests: {receipt['distinct_live_requests']}")
    if "max_live_calls" in receipt:
        lines.append(f"Live-call cap: {receipt['max_live_calls']}")
    lines.extend([f"Seeds: {len(seeds)}; seed file SHA-256: `{seed_sha256}`", "",
                  f"Receipt SHA-256: `{receipt['receipt_sha256']}`", "", "## Metrics", "",
                  "| Metric | Value |", "|---|---:|"])
    lines.extend(f"| {key} | {value} |" for key, value in metrics.items()
                 if isinstance(value, (str, int, float, bool)))
    lines.append("")
    (output_dir / f"{row}.md").write_text("\n".join(lines))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rra eval-v3")
    parser.add_argument("row", choices=ROWS)
    parser.add_argument("--role", choices=("eval_v3", "dev"), default="eval_v3")
    parser.add_argument("--seeds-file", type=Path)
    parser.add_argument("--freeze-tag")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/eval_v3")
    parser.add_argument("--nproc", type=int)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--replay", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--subset", action="store_true")
    parser.add_argument("--max-live-calls", type=int, default=DEFAULT_MAX_LIVE_CALLS)
    parser.add_argument("--estimate", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.max_live_calls < 0:
            raise ValueError("--max-live-calls must be non-negative")
        if args.estimate and (args.row != "b4" or args.role != "dev" or args.live or args.replay):
            raise ValueError("--estimate is available only for b4 in role dev")
        if args.subset and (args.role != "dev" or args.row != "b4"):
            raise ValueError("--subset is only available for b4 in role dev")
        if args.role == "dev":
            if args.seeds_file is None:
                raise ValueError("--seeds-file is required for role dev")
            seed_path = args.seeds_file.resolve()
            allowed = {DEV_SEEDS_PATH.resolve(), DIAG_SUBSET_PATH.resolve()}
            if args.subset and seed_path not in allowed:
                raise ValueError("--subset requires the dev seed file or the registered diag subset")
        else:
            if args.seeds_file is not None:
                raise ValueError("--seeds-file is only accepted for role dev")
            seed_path = ROOT / "config/eval_seeds_v3.json"
        seeds, digest = load_seed_file(seed_path, args.role, freeze_tag=args.freeze_tag)
        indices = None
        if args.subset:
            dev_seeds = json.loads(DEV_SEEDS_PATH.read_text())["seeds"]
            subset_seeds = json.loads(DIAG_SUBSET_PATH.read_text())["seeds"]
            index_by_seed = {seed: index for index, seed in enumerate(dev_seeds)}
            if any(seed not in index_by_seed for seed in subset_seeds):
                raise ValueError("diag subset contains a seed absent from the dev seed file")
            seeds = subset_seeds
            indices = [index_by_seed[seed] for seed in seeds]
            seed_path = DIAG_SUBSET_PATH
            digest = _sha_file(DIAG_SUBSET_PATH)
        if args.estimate:
            print(json.dumps({"unique_requests": estimate_b4(seeds, indices)}, sort_keys=True))
            return 0
        if args.row == "b4" and not (args.replay or args.live):
            raise ValueError("b4 runs require --replay or --live")
        receipt = run_row(args.row, seeds=seeds, seed_path=seed_path, seed_sha256=digest,
                          output_dir=args.output_dir, role=args.role, nproc=args.nproc,
                          replay=args.replay, live=args.live, subset=args.subset,
                          max_live_calls=args.max_live_calls, indices=indices)
        print(json.dumps({"row": args.row, "status": receipt["status"],
                          "receipt_sha256": receipt["receipt_sha256"]}, sort_keys=True))
        return 3 if receipt["status"] == "incomplete" else 0
    except LiveBudgetExceeded as exc:
        print(f"eval-v3 error: {exc}", file=sys.stderr)
        return 3
    except subprocess.CalledProcessError:
        print("eval-v3 error: git command failed", file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        from rra.llm.providers import ReplayCacheMiss

        if isinstance(exc, ReplayCacheMiss):
            print(f"ReplayCacheMiss: {exc}", file=sys.stderr)
            return 2
        print(f"eval-v3 error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
