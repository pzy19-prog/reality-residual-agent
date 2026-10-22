import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

_spec = importlib.util.spec_from_file_location("nemotron_smoke", Path(__file__).parents[1] / "scripts" / "nemotron_smoke.py")
nemotron_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nemotron_smoke)


def test_smoke_stops_on_403_and_redacts_key(monkeypatch, capsys):
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key-value")
    calls = {"propose": 0}

    class FakeProvider:
        last_http_status = 403
        last_latency_seconds = 0.25

    class FakeProposer:
        def __init__(self, provider):
            self.provider = provider

        def propose(self, evidence_packet, context_text):
            calls["propose"] += 1
            return SimpleNamespace(
                error="HTTP 403 response body echoed secret-key-value",
                items=[],
            )

    monkeypatch.setattr(nemotron_smoke, "NvidiaNimProvider", FakeProvider)
    monkeypatch.setattr(nemotron_smoke, "HypothesisProposer", FakeProposer)
    assert nemotron_smoke.main() == 2
    assert calls["propose"] == 1
    output = capsys.readouterr().out
    assert "secret-key-value" not in output
    result = json.loads(output)
    assert result["http_status"] == 403
    assert "[REDACTED]" in result["proposal_error"]
