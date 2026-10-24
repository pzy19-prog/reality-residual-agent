import io
import json
from email.message import EmailMessage
from urllib.error import HTTPError

import pytest

from rra.s2.dsl import STRUCTURE_IDS
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import ReplayCacheMiss, ReplayProvider, canonical_json, finalize_payload, request_sha256


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
    payload = finalize_payload(request, {})
    cache_file = tmp_path / f"{request_sha256(payload)}.json"
    cache_file.write_text(canonical_json({"request": payload, "response": response_body}), encoding="utf-8")
    replay = ReplayProvider(tmp_path)
    assert replay.complete(request) == replay.complete(request) == response_body
    from pytest import raises
    with raises(ReplayCacheMiss):
        replay.complete({"messages": []})


def test_adapter_propagates_replay_cache_miss():
    from pytest import raises

    class MissingReplay:
        def complete(self, request_body):
            raise ReplayCacheMiss("cache miss for request abc123")

    with raises(ReplayCacheMiss, match="abc123"):
        HypothesisProposer(MissingReplay()).propose({}, "")


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


def test_nim_cache_entry_is_replayable_from_adapter_request(tmp_path, monkeypatch):
    from rra.llm import providers
    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    response_body = response('{"items":[]}')

    class FakeHttpResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(response_body).encode()

    monkeypatch.setattr(providers, "urlopen", lambda request, timeout: FakeHttpResponse())
    provider = providers.NvidiaNimProvider(cache_dir=tmp_path)
    request_body = {"messages": [{"role": "user", "content": "synthetic"}]}
    assert provider.complete(request_body) == response_body
    assert providers.ReplayProvider(tmp_path).complete(request_body) == response_body


def test_nvidia_provider_rejects_small_token_limit(monkeypatch):
    import pytest
    from rra.llm.providers import NvidiaNimProvider
    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    with pytest.raises(ValueError, match="at least 1500"):
        NvidiaNimProvider(max_tokens=1499)


def test_nim_thinking_controls_are_in_canonical_payload_and_cache_key(tmp_path, monkeypatch):
    from rra.llm import providers

    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    seen = []

    class FakeHttpResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return b'{"model":"returned-model","choices":[{"message":{"content":"{}"},"finish_reason":"stop"}]}'

    def fake_urlopen(request, timeout):
        seen.append(json.loads(request.data))
        return FakeHttpResponse()
    monkeypatch.setattr(providers, "urlopen", fake_urlopen)
    base_request = {"messages": [{"role": "system", "content": "system prompt"}]}
    variants = (
        providers.NvidiaNimProvider(cache_dir=tmp_path, chat_template_kwargs={"enable_thinking": False}),
        providers.NvidiaNimProvider(cache_dir=tmp_path, chat_template_kwargs=None, no_think=True),
    )
    for provider in variants:
        provider.complete(base_request)
    assert seen[0]["chat_template_kwargs"] == {"enable_thinking": False}
    default_provider = providers.NvidiaNimProvider(cache_dir=tmp_path)
    default_provider.complete(base_request)
    assert seen[2]["chat_template_kwargs"] == {"enable_thinking": False}
    assert seen[1]["messages"][0]["content"].startswith("/no_think\n")
    assert providers.request_sha256(seen[0]) != providers.request_sha256(seen[1])
    assert len(list(tmp_path.glob("*.json"))) == 2


def _http_error(code, headers=None, body=b"secret-body"):
    return HTTPError("https://example.invalid", code, "err", headers, io.BytesIO(body))


def _retry_headers(value):
    headers = EmailMessage()
    headers["Retry-After"] = str(value)
    return headers


def _install_live(monkeypatch, tmp_path, urlopen):
    from rra.llm import providers

    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(providers, "urlopen", urlopen)
    providers.disable_live_outage()
    return providers, providers.NvidiaNimProvider(cache_dir=tmp_path)


def test_repeated_500_writes_one_error_record_and_replay_matches(tmp_path, monkeypatch):
    calls = {"n": 0}

    def urlopen(request, timeout):
        calls["n"] += 1
        raise _http_error(500, body=b"upstream secret")

    providers, provider = _install_live(monkeypatch, tmp_path, urlopen)
    request = {"messages": [{"role": "user", "content": "synthetic"}]}
    with pytest.raises(providers.CachedProviderError, match="^transient_exhausted$"):
        provider.complete(request)
    assert calls["n"] == 5
    record = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert record["error"] == {"class": "transient_exhausted", "http_status": 500}
    assert "upstream secret" not in json.dumps(record)
    assert "test-secret" not in json.dumps(record)
    with pytest.raises(providers.CachedProviderError, match="^transient_exhausted$"):
        providers.ReplayProvider(tmp_path).complete(request)


@pytest.mark.parametrize("status", [400, 302, 409, 422])
def test_deterministic_http_status_is_cached_without_retry(tmp_path, monkeypatch, status):
    calls = {"n": 0}

    def urlopen(request, timeout):
        calls["n"] += 1
        raise _http_error(status, body=b"do-not-store")

    providers, provider = _install_live(monkeypatch, tmp_path, urlopen)
    request = {"messages": [{"role": "user", "content": f"status-{status}"}]}
    with pytest.raises(providers.CachedProviderError, match="^deterministic$"):
        provider.complete(request)
    assert calls["n"] == 1
    record = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert record["error"] == {"class": "deterministic", "http_status": status}
    assert "do-not-store" not in json.dumps(record)


def test_retry_after_is_capped_and_preferred_over_backoff(tmp_path, monkeypatch):
    from rra.llm import providers

    sleeps = []
    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: sleeps.append(seconds))
    providers.disable_live_outage()
    plan = {"left": [("429", "7"), ("200", None), ("429", "120"), ("200", None)]}

    def urlopen(request, timeout):
        kind, retry_after = plan["left"].pop(0)
        if kind == "200":
            class Response:
                status = 200
                headers = None
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self):
                    return b'{"choices":[{"message":{"content":"{}"}}]}'
            return Response()
        raise _http_error(429, headers=_retry_headers(retry_after), body=b"slow-down")

    monkeypatch.setattr(providers, "urlopen", urlopen)
    provider = providers.NvidiaNimProvider(cache_dir=tmp_path)
    provider.complete({"messages": [{"role": "user", "content": "first"}]})
    provider.complete({"messages": [{"role": "user", "content": "second"}]})
    assert sleeps == [7.0, 60.0]


def test_non_json_200_is_retried_then_cached_as_transient(tmp_path, monkeypatch):
    calls = {"n": 0}

    def urlopen(request, timeout):
        calls["n"] += 1
        class Response:
            status = 200
            headers = None
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b"not-json-secret"
        return Response()

    providers, provider = _install_live(monkeypatch, tmp_path, urlopen)
    request = {"messages": [{"role": "user", "content": "bad-json"}]}
    with pytest.raises(providers.CachedProviderError, match="^transient_exhausted$"):
        provider.complete(request)
    assert calls["n"] == 5
    record = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert record["error"] == {"class": "transient_exhausted", "http_status": 200}
    assert "not-json-secret" not in json.dumps(record)


def test_auth_failure_stops_without_a_cache_record(tmp_path, monkeypatch):
    calls = {"n": 0}

    def urlopen(request, timeout):
        calls["n"] += 1
        raise _http_error(401, body=b"credential-body")

    providers, provider = _install_live(monkeypatch, tmp_path, urlopen)
    with pytest.raises(SystemExit, match="401") as exc_info:
        provider.complete({"messages": [{"role": "user", "content": "auth"}]})
    assert calls["n"] == 1
    assert list(tmp_path.glob("*.json")) == []
    assert "credential-body" not in str(exc_info.value)


def test_ten_consecutive_error_records_stop_and_a_success_resets(tmp_path, monkeypatch):
    from rra.llm import providers

    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: None)
    mode = {"ok": False}

    def urlopen(request, timeout):
        if mode["ok"]:
            class Response:
                status = 200
                headers = None
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self):
                    return b'{"choices":[{"message":{"content":"{}"}}]}'
            return Response()
        raise _http_error(400, body=b"nope")

    monkeypatch.setattr(providers, "urlopen", urlopen)
    providers.reset_live_outage()
    try:
        provider = providers.NvidiaNimProvider(cache_dir=tmp_path)
        for index in range(9):
            with pytest.raises(providers.CachedProviderError):
                provider.complete({"messages": [{"role": "user", "content": f"err-{index}"}]})
        mode["ok"] = True
        provider.complete({"messages": [{"role": "user", "content": "ok"}]})
        mode["ok"] = False
        for index in range(9):
            with pytest.raises(providers.CachedProviderError):
                provider.complete({"messages": [{"role": "user", "content": f"again-{index}"}]})
        with pytest.raises(providers.LiveOutageStop):
            provider.complete({"messages": [{"role": "user", "content": "tenth-after-success"}]})
        assert len(list(tmp_path.glob("*.json"))) == 20
    finally:
        providers.disable_live_outage()
