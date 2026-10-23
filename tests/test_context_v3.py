import re

import pytest

from rra.eval.context_v3 import (
    FAULT_HYPOTHESIS_IDS, STRUCTURE_IDS, VARIANTS, compatible_families,
    content_sha256, freeze_context, generate_context, select_template_family,
    verify_frozen_context,
)
from rra.s2.dsl import (
    STRUCTURE_IDS as DSL_STRUCTURE_IDS, structure_from_id, structure_id,
)

MAPPABLE = (
    "SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP", "ACTUATOR_DELAY",
    "SENSOR_STUCK", "SENSOR_SPIKE_BURST", "OBJECT_MISSING", "BELT_STOP",
    ("SENSOR_BIAS", "SPEED_STEP"), "SECOND_DYNAMICS_CHANGE",
)


@pytest.mark.parametrize("cause", MAPPABLE)
@pytest.mark.parametrize("variant", VARIANTS)
def test_all_registered_causes_generate_all_variants_without_numeric_leaks(cause, variant):
    text = generate_context("episode-a", 17, variant, cause, hidden_values=(1.2345, 4))
    assert not re.search(r"\d", text)


def test_seed_determinism_and_frozen_hash_fail_closed():
    a = freeze_context("episode-1", 8, "HELPFUL_TEXT_CONTEXT", "VELOCITY_OFFSET")
    b = freeze_context("episode-1", 8, "HELPFUL_TEXT_CONTEXT", "VELOCITY_OFFSET")
    assert a == b
    assert a.content_sha256 == content_sha256(a.text)
    verify_frozen_context(a)
    with pytest.raises(ValueError, match="frozen context mismatch"):
        verify_frozen_context(a, text=a.text + " ")
    with pytest.raises(ValueError, match="frozen context mismatch"):
        verify_frozen_context(a, expected_sha256="0" * 64)


@pytest.mark.parametrize("cause", MAPPABLE)
def test_misleading_family_is_incompatible(cause):
    selected = select_template_family(23, "MISLEADING_TEXT_CONTEXT", cause)
    assert selected not in compatible_families(cause)


def test_registered_ids_are_exactly_fourteen_structures_and_six_faults():
    assert len(STRUCTURE_IDS) == 14
    assert len(FAULT_HYPOTHESIS_IDS) == 6
    assert STRUCTURE_IDS == DSL_STRUCTURE_IDS == (
        "SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP", "ACTUATOR_DELAY",
        "AND(SENSOR_BIAS,VELOCITY_OFFSET)", "AND(SENSOR_BIAS,SPEED_STEP)",
        "AND(SENSOR_BIAS,ACTUATOR_DELAY)", "AND(VELOCITY_OFFSET,SPEED_STEP)",
        "AND(VELOCITY_OFFSET,ACTUATOR_DELAY)", "AND(SPEED_STEP,ACTUATOR_DELAY)",
        "AND(SENSOR_BIAS,VELOCITY_OFFSET,SPEED_STEP)",
        "AND(SENSOR_BIAS,VELOCITY_OFFSET,ACTUATOR_DELAY)",
        "AND(SENSOR_BIAS,SPEED_STEP,ACTUATOR_DELAY)",
        "AND(VELOCITY_OFFSET,SPEED_STEP,ACTUATOR_DELAY)",
    )
    for identifier in DSL_STRUCTURE_IDS:
        assert structure_id(structure_from_id(identifier)) == identifier


def test_second_dynamics_change_uses_speed_family_helpful_and_sensor_actuator_misleading():
    assert select_template_family(0, "HELPFUL_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE") == "TXT-MOTOR-SERVICE"
    assert select_template_family(1, "HELPFUL_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE") == "TXT-PACKAGE-SLIP"
    assert select_template_family(0, "MISLEADING_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE") == "TXT-SENSOR-CAL"
    assert select_template_family(1, "MISLEADING_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE") == "TXT-ACTUATOR-SLOW"
    assert "MOTOR" in generate_context("e", 0, "HELPFUL_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE") or \
        "motor" in generate_context("e", 0, "HELPFUL_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE")


def test_episode_freezes_all_four_variants_with_content_hashes():
    from rra.eval.context_v3 import freeze_episode_contexts
    records = freeze_episode_contexts("episode-b", 9, "SENSOR_BIAS")
    assert set(records) == set(VARIANTS)
    assert all(record.content_sha256 == content_sha256(record.text) for record in records.values())
    assert {key: value.content_sha256 for key, value in records.items()} == {
        "NO_TEXT_CONTEXT": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "HELPFUL_TEXT_CONTEXT": "71546583b50f918a18c44b3f45ab885c894468c6a4d7e1a9853674518056d017",
        "IRRELEVANT_TEXT_CONTEXT": "41a5c9d71cd518bbd257d5ba107a2fa0dc7b959daf2a63f0080a8550ac8e161e",
        "MISLEADING_TEXT_CONTEXT": "6b4183a2516a142d7ec4f88b9f3a5951489b1847fcb124963f8c0a90f0c475d9",
    }
