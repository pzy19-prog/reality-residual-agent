import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import b4_probe
import check_dev_b4_seeds


def test_selection_uses_registered_order_for_ties():
    results = {mode: {"valid_nonempty_items": 2} for mode in b4_probe.FORMAT_MODES}
    assert b4_probe._select_format_mode(results) == "json_object"
    results["nvext_guided_json"]["valid_nonempty_items"] = 3
    assert b4_probe._select_format_mode(results) == "nvext_guided_json"


def test_probe_excludes_truncation_and_error_does_not_reuse_response(tmp_path, monkeypatch):
    monkeypatch.setattr(b4_probe, "ROOT", tmp_path)
    monkeypatch.setattr(b4_probe, "_collect_requests", lambda _k: [
        {"evidence_packet": {}, "s2_summary": {}},
        {"evidence_packet": {}, "s2_summary": {}},
    ])
    monkeypatch.setenv("NVIDIA_API_KEY", "test-only")

    class FakeProvider:
        def __init__(self, **_kwargs):
            self.calls = 0
            self.last_response_body = None
            self.last_http_status = None
            self.last_latency_seconds = 0.01

        def complete(self, _request):
            self.calls += 1
            if self.calls == 1:
                self.last_http_status = 200
                self.last_response_body = {
                    "model": "fake-model",
                    "choices": [{"finish_reason": "length", "message": {"content": json.dumps({
                        "items": [{"hypothesis_id": "SENSOR_BIAS", "rationale": "x",
                                   "evidence_refs": []}]
                    })}}],
                }
                return self.last_response_body
            raise RuntimeError("simulated provider error")

    monkeypatch.setattr(b4_probe, "NvidiaNimProvider", FakeProvider)
    assert b4_probe.main(["--live", "--max-calls", "30"]) == 0
    body = json.loads((tmp_path / "artifacts/s2/b4-probe.json").read_text())
    assert body["selected_format_mode"] == "json_object"
    assert body["selection_rule"] == "A06 §3.2 / A07 §3.2"
    for result in body["modes"].values():
        assert result["valid_nonempty_items"] == 0
        assert result["finish_reason_distribution"] == {"error_record": 1, "length": 1}
        assert result["served_models"] == {"fake-model": 1}
        assert result["http_errors"] == 0


def test_live_probe_refuses_existing_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(b4_probe, "ROOT", tmp_path)
    monkeypatch.setattr(b4_probe, "_collect_requests", lambda _k: [
        {"evidence_packet": {}, "s2_summary": {}}
    ])
    artifact = tmp_path / "artifacts/s2/b4-probe.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("keep")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        b4_probe.main(["--live", "--max-calls", "30"])
    assert exc.value.code == 2
    assert artifact.read_text() == "keep"


def test_dev_seed_checker_accepts_subset_and_rejects_outside_or_excluded():
    diag = {1, 2, 3, 20, 21, 22}
    valid = {"seed_identity": {"path": check_dev_b4_seeds.DIAG_PATH,
                               "values": sorted(diag)},
             "episodes": [{"seed": 1}, {"seed": 20}]}
    assert check_dev_b4_seeds.check_artifact(valid, diag) == []
    outside = {**valid, "episodes": [{"seed": 999}]}
    assert any("outside diag subset" in error
               for error in check_dev_b4_seeds.check_artifact(outside, diag))
    excluded = {**valid, "episodes": [{"seed": 28}]}
    assert any("seed % 19 == 9" in error
               for error in check_dev_b4_seeds.check_artifact(excluded, diag))
    wrong_identity = {**valid, "seed_identity": {"path": "elsewhere", "values": []}}
    assert check_dev_b4_seeds.check_artifact(wrong_identity, diag)
