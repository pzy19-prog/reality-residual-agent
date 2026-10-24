from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from rra.eval import b4_dev, final_v3
from test_holdout import assert_final_seed_rule


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts/gen_eval_v3_seeds.py"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q")
    git(root, "config", "user.name", "Eval Test")
    git(root, "config", "user.email", "eval-test@example.invalid")
    (root / "tracked.txt").write_text("baseline\n")
    git(root, "add", "tracked.txt")
    git(root, "commit", "-qm", "baseline")


def generate(root: Path, tag: str = "freeze") -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(GENERATOR), "--freeze-tag", tag, "--root", str(root)],
                          capture_output=True, text=True)


def test_seed_generator_creates_100_unique_in_range_without_printing_values(tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", "freeze")
    result = generate(tmp_path)
    assert result.returncode == 0
    payload = json.loads((tmp_path / "config/eval_seeds_v3.json").read_text())
    seeds = payload["seeds"]
    assert payload["schema_version"] == "rra.eval-seeds.v3"
    assert payload["role"] == "eval_v3" and payload["count"] == 100
    assert payload["range"] == [10000, 2147483647]
    assert len(seeds) == len(set(seeds)) == 100
    assert all(10000 <= seed < 2147483647 for seed in seeds)
    assert result.stdout.startswith("count=100 sha256=")
    digest = result.stdout.strip().split("sha256=", 1)[1]
    visible = result.stdout.replace(digest, "") + result.stderr.replace(digest, "")
    assert all(str(seed) not in visible for seed in seeds)
    assert result.stderr == ""


@pytest.mark.parametrize("failure", ["tag_mismatch", "dirty_tree", "target_exists"])
def test_seed_generator_refuses_unsafe_states_without_writing(tmp_path, failure):
    init_repo(tmp_path)
    git(tmp_path, "tag", "freeze")
    if failure == "tag_mismatch":
        (tmp_path / "tracked.txt").write_text("later commit\n")
        git(tmp_path, "add", "tracked.txt")
        git(tmp_path, "commit", "-qm", "later")
    elif failure == "dirty_tree":
        (tmp_path / "dirty.txt").write_text("dirty\n")
    else:
        (tmp_path / "config").mkdir()
        (tmp_path / "config/eval_seeds_v3.json").write_text("{}\n")
    result = generate(tmp_path)
    assert result.returncode != 0
    assert not (tmp_path / "config/eval_seeds_v3.json").exists() or failure == "target_exists"
    assert "seeds" not in result.stdout


def test_eval_guard_rejects_source_changes_after_freeze(tmp_path):
    init_repo(tmp_path)
    git(tmp_path, "tag", "freeze")
    config = tmp_path / "config"
    config.mkdir()
    seed_path = config / "eval_seeds_v3.json"
    seed_path.write_text(json.dumps({
        "schema_version": "rra.eval-seeds.v3", "role": "eval_v3", "count": 100,
        "range": [10000, 2147483647], "generator": "secrets.SystemRandom().sample",
        "freeze_tag": "freeze", "freeze_commit": git(tmp_path, "rev-parse", "HEAD"),
        "seeds": list(range(10000, 10100)),
    }) + "\n")
    git(tmp_path, "add", "config/eval_seeds_v3.json")
    git(tmp_path, "commit", "-qm", "seed file")
    (tmp_path / "src.py").write_text("changed\n")
    git(tmp_path, "add", "src.py")
    git(tmp_path, "commit", "-qm", "source changed")
    with pytest.raises(ValueError, match="outside the eval allowlist"):
        final_v3.load_seed_file(seed_path, "eval_v3", freeze_tag="freeze", root=tmp_path)


@pytest.mark.parametrize("with_seed_file", [False, True])
def test_holdout_seed_rule_before_and_after_seed_commit(tmp_path, with_seed_file):
    init_repo(tmp_path)
    if with_seed_file:
        path = tmp_path / "config/eval_seeds_v3.json"
        path.parent.mkdir()
        data = {"schema_version": "rra.eval-seeds.v3", "role": "eval_v3", "count": 100,
                "range": [10000, 2147483647], "seeds": list(range(10000, 10100))}
        path.write_text(json.dumps(data) + "\n")
        git(tmp_path, "add", "config/eval_seeds_v3.json")
        git(tmp_path, "commit", "-qm", "introduce eval seeds")
    assert_final_seed_rule(tmp_path)


def test_b4_live_call_limit_stops_before_exceeding_cap(monkeypatch):
    calls = {"n": 0}

    class Live:
        model = "test-model"
        max_tokens = 1800
        chat_template_kwargs = {"enable_thinking": False}
        no_think = False
        last_http_status = None

        def __init__(self, *args, **kwargs):
            pass

        def complete(self, request_body):
            calls["n"] += 1
            return {"choices": [{"message": {"content": "{\"items\": []}"}}]}

    monkeypatch.setattr(b4_dev, "NvidiaNimProvider", Live)
    with final_v3._LiveBudgetScope(1):
        provider = b4_dev.NvidiaNimProvider()
        provider.complete({"messages": [{"role": "user", "content": "one"}]})
        with pytest.raises(final_v3.LiveBudgetExceeded):
            provider.complete({"messages": [{"role": "user", "content": "two"}]})
    assert calls["n"] == 1
    calls["n"] = 0
    body = {"messages": [{"role": "user", "content": "same"}]}
    with final_v3._LiveBudgetScope(1):
        provider = b4_dev.NvidiaNimProvider()
        provider.complete(body)
        provider.complete(dict(body))
    assert calls["n"] == 2


def test_completed_text_condition_pairs_count_strict_then_tiebreak(monkeypatch):
    def episode(*args, **kwargs):
        return {"variant": kwargs.get("s2_variant")}

    monkeypatch.setattr(b4_dev, "run_episode", episode)
    with final_v3._LiveBudgetScope(5) as budget:
        b4_dev.run_episode(s2_variant="B4_STRICT")
        assert budget.completed_pairs == 0
        b4_dev.run_episode(s2_variant="B4_TIEBREAK")
        assert budget.completed_pairs == 1
        b4_dev.run_episode(s2_variant="B4_STRICT")
        b4_dev.run_episode(s2_variant="B3")
        assert budget.completed_pairs == 1


def test_b4_limit_writes_incomplete_row_receipt(monkeypatch, tmp_path):
    def limited(*args, **kwargs):
        raise final_v3.LiveBudgetExceeded("maximum reached")

    monkeypatch.setattr(b4_dev, "run_b4_dev", limited)
    seeds_file = tmp_path / "dev.json"
    seeds_file.write_text('{"seeds": [42]}\n')
    receipt = final_v3.run_row(
        "b4", seeds=[42], seed_path=seeds_file, seed_sha256="test-hash",
        output_dir=tmp_path / "out", role="dev", live=True, max_live_calls=0,
    )
    saved = json.loads((tmp_path / "out/b4.json").read_text())
    assert receipt["status"] == saved["status"] == "incomplete"
    assert saved["reason"] == "max_live_calls_reached"
    assert saved["max_live_calls"] == 0
    assert saved["completed_text_condition_pairs"] == 0
    assert saved["distinct_live_requests"] == 0


def test_max_live_calls_default_is_2500(monkeypatch, tmp_path):
    seen = {}

    def fake_run_row(row, **kwargs):
        seen["row"] = row
        seen.update(kwargs)
        return {"status": "complete", "metrics": {}, "receipt_sha256": "digest"}

    monkeypatch.setattr(final_v3, "run_row", fake_run_row)
    monkeypatch.setattr(final_v3, "load_seed_file", lambda *args, **kwargs: ([11], "digest"))
    code = final_v3.main([
        "b2", "--role", "dev", "--seeds-file", str(tmp_path / "seeds.json"),
        "--output-dir", str(tmp_path / "out"),
    ])
    assert code == 0
    assert seen["max_live_calls"] == 2500


def test_live_rerun_keeps_prior_distinct_requests_inside_the_cap(monkeypatch, tmp_path):
    calls = {"n": 0}

    class Live:
        model = "test-model"
        max_tokens = 1800
        chat_template_kwargs = {"enable_thinking": False}
        no_think = False
        last_http_status = None

        def __init__(self, *args, **kwargs):
            pass

        def complete(self, request_body):
            calls["n"] += 1
            return {"choices": [{"message": {"content": "{\"items\": []}"}}]}

    def one_new_request(*args, **kwargs):
        b4_dev.NvidiaNimProvider().complete({"messages": [{"role": "user", "content": "new"}]})
        return {"metrics": {}, "episodes": [], "llm_calls": 1}

    monkeypatch.setattr(b4_dev, "NvidiaNimProvider", Live)
    monkeypatch.setattr(b4_dev, "run_b4_dev", one_new_request)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "b4.json").write_text(json.dumps({"distinct_live_requests": 2500}) + "\n")
    result = final_v3._run_b4(
        tmp_path / "seeds.json", output_dir, replay=False, live=True, subset=False,
        max_live_calls=2500, nproc=1,
    )
    assert result["status"] == "incomplete"
    assert result["reason"] == "max_live_calls_reached"
    assert result["distinct_live_requests"] == 2500
    assert calls["n"] == 0


def test_estimate_refuses_eval_role_without_reading_seeds(capsys):
    code = final_v3.main(["b4", "--estimate"])
    assert code == 2
    assert "role dev" in capsys.readouterr().err
    assert not (ROOT / "config/eval_seeds_v3.json").exists()

