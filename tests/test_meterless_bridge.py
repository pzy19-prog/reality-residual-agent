"""L6 Meterless persistence: unit tests on a fake bridge, plus live tests behind RRA_METERLESS_LIVE=1."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from rra.sponsor import meterless as m

ROOT = Path(__file__).resolve().parents[1]
FAKE = [sys.executable, str(Path(__file__).with_name("_fake_meterless_bridge.py"))]
LIVE = os.environ.get("RRA_METERLESS_LIVE") == "1" and m.bridge_available()
live = pytest.mark.skipif(not LIVE, reason="needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1")


def synthetic_receipt(n: int = 3) -> dict:
    decisions, trace = [], []
    for i in range(n):
        decisions.append({"time": 1.0 + i, "target_id": i, "action": "PAUSE_AND_REOBSERVE",
                          "gate_reason": "no passing hypothesis", "faults": [], "pause_seconds": 0.0})
        trace.append({
            "seed": 7, "target_id": i, "sim_time": 1.0 + i, "first_observed_at": 0.5,
            "window_remaining_time": 0.2, "planned_window_end": 2.0, "n_usable_before_upgrade": 4,
            "n_usable_after_upgrade": 1, "n_usable_total": 5,
            "fits": [{"structure": ["SENSOR_BIAS"], "fit": True, "rmse": 0.01, "n_usable": 5,
                      "parameters": {"sensor_bias": 0.2}}],
            "verified": [], "passing": [], "gate": "no passing hypothesis", "action_time": None,
            "faults": [], "action": "PAUSE_AND_REOBSERVE",
            # evaluator-only fields appended by run_episode(include_s2_diagnostics=True)
            "terminal_status": "picked", "terminal_reason": "ok", "command_issued": True,
            "unsafe_witness": 0.001,
        })
    return {"system2_decisions": decisions, "s2_diagnostic_trace": trace, "receipt_sha256": "ab" * 32,
            "evaluator_objects": [{"target_id": 0, "command_issued": True}]}


def manifest_for(receipt: dict, episode_id: str = "ep-007") -> dict:
    return m.build_manifest(episode_id=episode_id, seed=7, case=["SENSOR_BIAS"], fault_family=None,
                            run_episode_kwargs={"compensation": True}, base_git_sha="0" * 40, receipt=receipt)


def ledger(store: Path) -> list[dict]:
    return [json.loads(line) for line in (store / "ledger.jsonl").read_text().splitlines() if line]


def test_canonical_json_is_order_independent():
    assert m.canonical_json({"b": 1, "a": [1.5, None]}) == '{"a":[1.5,null],"b":1}'
    assert m.sha256_text(m.canonical_json({"a": 1, "b": 2})) == m.sha256_text(m.canonical_json({"b": 2, "a": 1}))


def test_run_records_strip_hidden_fields_and_have_fixed_key_set():
    records = m.build_run_records("ep-007", synthetic_receipt())
    assert len(records) == 3
    for index, record in enumerate(records):
        assert set(record) == m.RUN_RECORD_KEYS
        assert record["schema"] == m.RUN_SCHEMA and record["decision_index"] == index
        assert not set(m.iter_keys(record)) & m.FORBIDDEN_RUN_KEYS
        assert not set(record["diagnostic"]) & m.HIDDEN_DIAGNOSTIC_KEYS
        assert "sensor_bias" in record["diagnostic"]["fits"][0]["parameters"]  # fitted, not truth


def test_unknown_key_in_record_is_refused():
    receipt = synthetic_receipt()
    receipt["s2_diagnostic_trace"][0]["new_eval_field"] = 1
    with pytest.raises(m.LeakError):
        m.build_run_records("ep-007", receipt)


def test_whitelist_excludes_hidden_keys():
    assert not m.ALLOWED_RUN_KEYS & m.FORBIDDEN_RUN_KEYS


def test_run_records_do_not_mutate_receipt():
    receipt = synthetic_receipt()
    before = copy.deepcopy(receipt)
    m.build_run_records("ep-007", receipt)
    assert receipt == before


def test_pairing_length_mismatch_stops():
    receipt = synthetic_receipt()
    receipt["s2_diagnostic_trace"].pop()
    with pytest.raises(m.PairingError):
        m.build_run_records("ep-007", receipt)


def test_hard_fault_latch_decisions_store_null_diagnostic():
    receipt = synthetic_receipt(2)
    latch = {"time": 1.0, "target_id": 0, "trigger": "hard_fault_latch", "action": "HUMAN_ESCALATION",
             "gate_reason": "HARD_FAULT_LATCH", "faults": ["SENSOR_STUCK"], "pause_seconds": 0.0}
    receipt["system2_decisions"].insert(1, latch)
    records = m.build_run_records("ep-007", receipt)
    assert [r["decision_index"] for r in records] == [0, 1, 2]
    assert records[1]["diagnostic"] is None
    assert records[0]["diagnostic"]["target_id"] == 0 and records[2]["diagnostic"]["target_id"] == 1
    assert all(set(r) == m.RUN_RECORD_KEYS for r in records)


def test_undiagnosed_decision_without_latch_trigger_stops():
    receipt = synthetic_receipt(2)
    receipt["system2_decisions"].append(dict(receipt["system2_decisions"][0], time=9.0))
    with pytest.raises(m.PairingError):
        m.build_run_records("ep-007", receipt)


def test_pairing_requires_diagnostics():
    receipt = synthetic_receipt()
    del receipt["s2_diagnostic_trace"]
    with pytest.raises(m.PairingError):
        m.build_run_records("ep-007", receipt)


def test_pairing_misaligned_rows_stop():
    receipt = synthetic_receipt()
    receipt["s2_diagnostic_trace"][1]["target_id"] = 99
    with pytest.raises(m.PairingError):
        m.build_run_records("ep-007", receipt)


def test_hidden_key_inside_decision_is_refused():
    receipt = synthetic_receipt()
    receipt["system2_decisions"][0]["evaluator_objects"] = []
    with pytest.raises(m.LeakError):
        m.build_run_records("ep-007", receipt)


def test_manifest_key_set_and_decision_hash():
    receipt = synthetic_receipt()
    manifest = manifest_for(receipt)
    assert set(manifest) == m.MANIFEST_KEYS
    assert manifest["decisions_sha256"] == m.sha256_text(m.canonical_json(receipt["system2_decisions"]))
    assert manifest["world_config"] == "v3/nominal"


def test_round_trip_on_fake_bridge(tmp_path):
    receipt = synthetic_receipt()
    result = m.persist_episode_run(receipt, manifest_for(receipt), store_dir=tmp_path / "ep-007",
                                   run_tag="t", bridge_cmd=FAKE)
    assert result.record_count == 3
    stored = m.read_episode(tmp_path / "ep-007", "ep-007", bridge_cmd=FAKE)
    assert [e["canonical_sha256"] for e in stored["runs"]] == result.record_sha256
    assert [e["raw_sha256"] for e in stored["runs"]] == result.record_sha256
    assert stored["manifest"]["canonical_sha256"] == result.manifest_sha256


def test_persist_refuses_populated_store(tmp_path):
    receipt = synthetic_receipt()
    m.persist_episode_run(receipt, manifest_for(receipt), store_dir=tmp_path / "s", run_tag="t", bridge_cmd=FAKE)
    with pytest.raises(FileExistsError):
        m.persist_episode_run(receipt, manifest_for(receipt), store_dir=tmp_path / "s", run_tag="t",
                              bridge_cmd=FAKE)


def test_cross_episode_read_is_refused_without_ledger_entry(tmp_path):
    store = tmp_path / "two"
    with m.MeterlessBridge(FAKE) as bridge:
        bridge.open(store, m.WRITE_CLOCK_START_MS)
        a = bridge.put("ep-A", "run", "{}")["memory_id"]
        bridge.put("ep-B", "run", "{}")
        before = ledger(store)
        with pytest.raises(m.BridgeError) as err:
            bridge.get("ep-B", a)
        assert err.value.code == "E_CROSS_EPISODE"
        assert ledger(store) == before
        assert not [e for e in ledger(store) if e["action"] == "read"]
        bridge.get("ep-A", a)
    reads = [e for e in ledger(store) if e["action"] == "read"]
    assert len(reads) == 1
    assert all(e["details"]["reader_episode_id"] == e["details"]["record_episode_id"] for e in reads)


def test_unknown_memory_id_and_bad_op(tmp_path):
    with m.MeterlessBridge(FAKE) as bridge:
        bridge.open(tmp_path / "s", m.WRITE_CLOCK_START_MS)
        with pytest.raises(m.BridgeError) as err:
            bridge.get("ep-A", "mem-404")
        assert err.value.code == "E_NOT_FOUND"
        with pytest.raises(m.BridgeError) as err:
            bridge.request("nope")
        assert err.value.code == "E_BAD_REQUEST"


def test_next_clock_continues_after_ledger(tmp_path):
    assert m.next_clock_ms(tmp_path) == m.WRITE_CLOCK_START_MS
    (tmp_path / "ledger.jsonl").write_text('{"timestamp": 1000005}\n{"timestamp": 1000003}\n')
    assert m.next_clock_ms(tmp_path) == 1000006


def test_replay_provider_slot_is_reserved():
    with pytest.raises(NotImplementedError):
        m.run_episode_from_manifest({}, provider=object())


def test_dependency_pins():
    package = json.loads((ROOT / "bridges/meterless/package.json").read_text())
    assert list(package["devDependencies"]) == ["tsx"]
    assert package["devDependencies"]["tsx"][0].isdigit()  # exact version, no range operator
    lock = json.loads((ROOT / "bridges/meterless/package-lock.json").read_text())
    assert lock["packages"]["node_modules/tsx"]["version"] == package["devDependencies"]["tsx"]
    setup = (ROOT / "scripts/setup_meterless.sh").read_text()
    assert 'PIN="1742dec56a66e58eef9dda2d2b865823758ca8cd"' in setup
    assert "npm ci --ignore-scripts" in setup


def test_vendor_and_node_modules_not_tracked():
    try:
        tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "bridges"], check=True,
                                 capture_output=True, text=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    assert not [p for p in tracked if "/vendor/" in p or "/node_modules/" in p]


@live
def test_live_round_trip_and_cross_episode(tmp_path):
    receipt = synthetic_receipt()
    store = tmp_path / "ep-007"
    result = m.persist_episode_run(receipt, manifest_for(receipt), store_dir=store, run_tag="live")
    stored = m.read_episode(store, "ep-007")
    assert [e["canonical_sha256"] for e in stored["runs"]] == result.record_sha256
    before = (store / "ledger.jsonl").read_bytes()
    with m.MeterlessBridge() as bridge:
        bridge.open(store, m.next_clock_ms(store))
        with pytest.raises(m.BridgeError) as err:
            bridge.get("ep-other", result.memory_ids[0])
        assert err.value.code == "E_CROSS_EPISODE"
    assert (store / "ledger.jsonl").read_bytes() == before
    reads = [e for e in ledger(store) if e["action"] == "read"]
    assert reads and all(e["details"]["reader_episode_id"] == e["details"]["record_episode_id"] for e in reads)
    for name in ("state.json", "ledger.jsonl"):
        text = (store / name).read_text()
        assert not [k for k in m.HIDDEN_DIAGNOSTIC_KEYS | {"evaluator_objects"} if k in text]


@live
def test_live_deterministic_across_directories(tmp_path):
    receipt = synthetic_receipt()
    a = m.persist_episode_run(receipt, manifest_for(receipt), store_dir=tmp_path / "a" / "ep-007", run_tag="live")
    b = m.persist_episode_run(receipt, manifest_for(receipt), store_dir=tmp_path / "b" / "ep-007", run_tag="live")
    assert (a.state_sha256, a.ledger_sha256) == (b.state_sha256, b.ledger_sha256)
    assert a.memory_ids == b.memory_ids


@live
def test_live_replay_of_a_real_episode(tmp_path):
    from rra.eval.framework import v3_world_config
    from rra.eval.scenarios import realize_episode
    from rra.evidence import run_episode

    seed = 0
    kwargs = {"compensation": True, "terminal_monitoring": "corrected", "system2_enabled": True,
              "include_s2_diagnostics": True}
    realization = realize_episode(seed, ("SENSOR_BIAS",))
    receipt = run_episode(v3_world_config("nominal"), seed, realization=realization, **kwargs)
    manifest = m.build_manifest(episode_id="ep-000", seed=seed, case=list(realization.structure),
                                fault_family=realization.fault_family, run_episode_kwargs=kwargs,
                                base_git_sha="0" * 40, receipt=receipt)
    m.persist_episode_run(receipt, manifest, store_dir=tmp_path / "ep-000", run_tag="live")
    result = m.replay_episode(tmp_path / "ep-000")
    assert result["decisions_match"] and result["receipt_match"]
    for record in m.read_episode(tmp_path / "ep-000", "ep-000")["runs"]:
        assert set(record["record"]) == m.RUN_RECORD_KEYS


@pytest.mark.parametrize("index,seed", [(16, 16), (18, 18)])
def test_hard_fault_latch_pairing_on_real_episodes(index, seed):
    from rra.eval.framework import v3_world_config
    from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
    from rra.evidence import run_episode

    n = len(composition_structures())
    realization = realize_episode(seed, (), FAULT_FAMILIES[index % 19 - n])
    receipt = run_episode(v3_world_config("nominal"), seed, realization=realization, compensation=True,
                          terminal_monitoring="corrected", system2_enabled=True, include_s2_diagnostics=True)
    records = m.build_run_records(m.episode_id_for(seed), receipt)
    assert len(records) == 13
    assert sum(r["diagnostic"] is None for r in records) == 10
    paired = [r for r in records if r["diagnostic"] is not None]
    assert len(paired) == 3
    for r in paired:
        assert r["decision"]["target_id"] == r["diagnostic"]["target_id"]
        assert r["decision"]["time"] == r["diagnostic"]["sim_time"]
    assert all(r["decision"]["trigger"] == "hard_fault_latch" for r in records if r["diagnostic"] is None)
    assert not set().union(*(set(m.iter_keys(r)) for r in records)) & m.FORBIDDEN_RUN_KEYS
