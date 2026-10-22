import json

from rra.eval.context_v3 import STRUCTURE_IDS
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import ReplayCacheMiss, ReplayProvider, canonical_json, request_sha256


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def complete(self, request_body):
        self.calls += 1
        return self.response


def response(content):
    return {"choices": [{"message": {"content": content}}]}


def test_valid_output_and_unknown_numeric_parameters_are_handled():
    provider = FakeProvider(response(json.dumps({"items": [
        {"hypothesis_id": STRUCTURE_IDS[0], "rationale": "Residual pattern supports the model.",
         "evidence_refs": ["observations[0]"], "bias": 0.23},
        {"hypothesis_id": "NOT_REGISTERED", "rationale": "Candidate.", "evidence_refs": [], "delta": 2},
    ]})))
    proposal = HypothesisProposer(provider).propose({"observations": []}, "helpful note")
    assert proposal.error is None
    assert [item.hypothesis_id for item in proposal.items] == [STRUCTURE_IDS[0]]
    assert proposal.receipt["unknown_ids"] == ["NOT_REGISTERED"]
    assert "$.items[0].bias" in proposal.receipt["ignored_numeric_parameters"]
    assert "$.items[1].delta" in proposal.receipt["ignored_numeric_parameters"]


def test_numeric_rationale_is_removed_and_logged():
    provider = FakeProvider(response(json.dumps({"items": [
        {"hypothesis_id": STRUCTURE_IDS[0], "rationale": "Offset equals 0.2.", "evidence_refs": []}
    ]})))
    proposal = HypothesisProposer(provider).propose({}, "")
    assert "0.2" not in proposal.items[0].rationale
    assert "$.items[0].rationale" in proposal.receipt["ignored_numeric_parameters"]


def test_invalid_json_returns_empty_proposal_without_raising():
    proposal = HypothesisProposer(FakeProvider(response("not json"))).propose({}, "")
    assert proposal.items == []
    assert proposal.error


def test_replay_provider_hit_is_deterministic_and_miss_raises(tmp_path):
    request = {"messages": [{"role": "user", "content": "synthetic"}]}
    response_body = {"choices": [{"message": {"content": '{"items":[]}'}}]}
    cache_file = tmp_path / f"{request_sha256(request)}.json"
    cache_file.write_text(canonical_json({"request": request, "response": response_body}), encoding="utf-8")
    replay = ReplayProvider(tmp_path)
    assert replay.complete(request) == replay.complete(request) == response_body
    from pytest import raises
    with raises(ReplayCacheMiss):
        replay.complete({"messages": []})


def test_adapter_makes_no_network_calls(monkeypatch):
    from urllib import request as urllib_request

    def forbidden(*args, **kwargs):
        raise AssertionError("network access attempted during pytest")
    monkeypatch.setattr(urllib_request, "urlopen", forbidden)
    HypothesisProposer(FakeProvider(response('{"items":[]}'))).propose({}, "")


def test_nvidia_provider_uses_env_key_and_writes_body_only_cache(tmp_path, monkeypatch):
    import io
    from rra.llm import providers

    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    payload = {"choices": [{"message": {"content": '{"items":[]}'}}]}

    class FakeHttpResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(payload).encode()

    seen = {}
    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data)
        return FakeHttpResponse()
    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    provider = providers.NvidiaNimProvider(cache_dir=tmp_path)
    result = provider.complete({"messages": [{"role": "user", "content": "synthetic"}]})
    assert result == payload
    assert seen["auth"] == "Bearer test-secret"
    assert seen["body"]["temperature"] == 0
    assert seen["body"]["max_tokens"] >= 1500
    cache_text = next(tmp_path.glob("*.json")).read_text(encoding="utf-8")
    assert "test-secret" not in cache_text
    assert "headers" not in cache_text and "wall_clock" not in cache_text
    assert set(json.loads(cache_text)) == {"request", "response"}


def test_nvidia_provider_rejects_small_token_limit(monkeypatch):
    import pytest
    from rra.llm.providers import NvidiaNimProvider
    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    with pytest.raises(ValueError, match="at least 1500"):
        NvidiaNimProvider(max_tokens=1499)
