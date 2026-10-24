import json

from rra.llm import adapter
from rra.llm.adapter import proposal_request, request_template_sha256
from rra.llm.providers import finalize_payload, request_sha256


def test_provider_payload_rounds_embedded_json_floats_to_six_places():
    settings = {"model": "test/model", "format_mode": "json_object"}

    def key(value):
        request = proposal_request({"observation": {"x": value}}, {"current_time": value})
        return request_sha256(finalize_payload(request, settings))

    assert key(0.12345611) == key(0.12345612)
    assert key(0.12345611) != key(0.12345711)


def test_format_modes_emit_the_registered_provider_shapes_and_distinct_templates():
    request = proposal_request("<EVIDENCE_PACKET>", "<S2_SUMMARY>")
    payloads = {
        mode: finalize_payload(request, {"format_mode": mode})
        for mode in ("json_object", "json_schema", "nvext_guided_json")
    }
    assert payloads["json_object"]["response_format"] == {"type": "json_object"}
    assert payloads["json_schema"]["response_format"]["json_schema"]["strict"] is True
    assert payloads["nvext_guided_json"]["nvext"]["guided_json"]
    assert len({request_template_sha256({"format_mode": mode}) for mode in payloads}) == 3


def test_request_template_hash_tracks_prompt_but_uses_fixed_evidence_markers(monkeypatch):
    settings = {"format_mode": "json_object"}
    original_request = proposal_request({"observations": [{"x": 1.2}]}, {"passing": []})
    second_request = proposal_request({"observations": [{"x": 8.7}]}, {"passing": []})
    original = request_template_sha256(settings, original_request)
    assert original == request_template_sha256(settings, second_request)
    monkeypatch.setattr(adapter, "SYSTEM_PROMPT", adapter.SYSTEM_PROMPT + " Updated.")
    changed = request_template_sha256(settings, proposal_request({"observations": []}, {"passing": []}))
    assert original != changed


def test_proposal_schema_enumerates_the_registered_structure_and_fault_ids():
    from rra.llm.schema import PROPOSAL_SCHEMA
    from rra.s2.dsl import STRUCTURE_IDS, FaultHypothesis

    item = PROPOSAL_SCHEMA["properties"]["items"]["items"]
    assert item["properties"]["hypothesis_id"]["enum"] == [
        *STRUCTURE_IDS, *(fault.value for fault in FaultHypothesis)]
    assert len(STRUCTURE_IDS) == 14 and len(FaultHypothesis) == 6
    assert item["required"] == ["hypothesis_id", "rationale", "evidence_refs"]
    assert item["additionalProperties"] is False
    assert PROPOSAL_SCHEMA["required"] == ["items"]
    assert PROPOSAL_SCHEMA["additionalProperties"] is False


def test_prompt_has_explicit_schema_example_and_context_is_inside_packet():
    request = proposal_request({"context": {"text": "frozen"}}, {"passing": []})
    system = request["messages"][0]["content"]
    user = json.loads(request["messages"][1]["content"])
    assert '"items":[{"hypothesis_id":"SENSOR_BIAS"' in system
    assert "registered IDs only" in system and "do not estimate numeric parameters" in system
    assert set(user) == {"evidence_packet", "s2_summary"}

