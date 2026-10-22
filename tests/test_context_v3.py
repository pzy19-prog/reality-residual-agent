import re

import pytest

from rra.eval.context_v3 import (
    FAULT_HYPOTHESIS_IDS, STRUCTURE_IDS, VARIANTS, compatible_families,
    content_sha256, freeze_context, generate_context, select_template_family,
    verify_frozen_context,
)

MAPPABLE = (
    "SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP", "ACTUATOR_DELAY",
    "SENSOR_STUCK", "SENSOR_SPIKE_BURST", "OBJECT_MISSING", "BELT_STOP",
    ("SENSOR_BIAS", "SPEED_STEP"),
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


def test_unknown_category_is_not_given_a_new_family():
    with pytest.raises(ValueError, match="UNKNOWN causal category"):
        generate_context("e", 0, "HELPFUL_TEXT_CONTEXT", "SECOND_DYNAMICS_CHANGE")


def test_episode_freezes_all_four_variants_with_content_hashes():
    from rra.eval.context_v3 import freeze_episode_contexts
    records = freeze_episode_contexts("episode-b", 9, "SENSOR_BIAS")
    assert set(records) == set(VARIANTS)
    assert all(record.content_sha256 == content_sha256(record.text) for record in records.values())
