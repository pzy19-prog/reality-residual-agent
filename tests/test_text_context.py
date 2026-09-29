import pytest

from rra.eval.framework import v3_world_config
from rra.eval.scenarios import realize_episode
from rra.eval.text_context import generate_text_context, validate_text_context
from rra.evidence import run_episode


def test_text_variants_are_deterministic_and_pass_leakage_validation():
    realization = realize_episode(28, ("SENSOR_BIAS", "SPEED_STEP"))
    variants = (
        "NO_TEXT_CONTEXT", "HELPFUL_TEXT_CONTEXT", "IRRELEVANT_TEXT_CONTEXT",
        "MISLEADING_TEXT_CONTEXT",
    )
    for variant in variants:
        text = generate_text_context(28, variant, [0.1, 0.2, 0.4])
        assert text == generate_text_context(28, variant, [0.1, 0.2, 0.4])
        validate_text_context(text, list(realization.recoverable.values()))


def test_text_variant_does_not_change_plant_or_noise():
    config = v3_world_config("nominal")
    realization = realize_episode(31, ("SENSOR_BIAS", "ACTUATOR_DELAY"))
    receipts = [
        run_episode(config, 31, True, realization=realization,
                    text_context=generate_text_context(31, variant), include_trace=True)
        for variant in ("NO_TEXT_CONTEXT", "HELPFUL_TEXT_CONTEXT", "IRRELEVANT_TEXT_CONTEXT", "MISLEADING_TEXT_CONTEXT")
    ]
    assert all(row["outcomes"] == receipts[0]["outcomes"] for row in receipts)
    assert all(row["failure_trace"] == receipts[0]["failure_trace"] for row in receipts)
    assert len({row["operational_text_context"] for row in receipts}) == 4


@pytest.mark.parametrize("text,secret", [
    ("SENSOR_BIAS value 0.237", 0.237),
    ("Scenario drift-high is active", 0.2),
    ("The bias is still present", 0.2),
    ("You should pause now", 0.2),
])
def test_leakage_validator_rejects_hidden_values_and_labels(text, secret):
    with pytest.raises(ValueError):
        validate_text_context(text, [secret])
