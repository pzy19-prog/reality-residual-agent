from dataclasses import fields
from math import isclose

from rra.evidence.policy import (
    PolicyCommandFeedback,
    PolicyKnownConfig,
    PolicyObservationSample,
    command_feedback,
    sanitize_config,
    sanitize_observation,
)
from rra.sim import World, WorldConfig


def test_policy_schemas_are_exact_whitelists():
    expected = {
        PolicyObservationSample: {
            "target_id", "step", "time", "observed_x", "observed_y",
            "nominal_x", "nominal_y", "nominal_speed",
        },
        PolicyKnownConfig: {"dt", "tolerance", "x_pick", "y_pick", "belt_speed"},
        PolicyCommandFeedback: {
            "command_id", "target_id", "issued_time", "execution_time",
            "accepted", "success", "reason_code",
        },
    }
    for schema, keys in expected.items():
        assert {field.name for field in fields(schema)} == keys


def test_sanitizer_returns_new_policy_type_without_truth_fields():
    raw = World(WorldConfig(), seed=3).observation()
    clean = sanitize_observation(raw)
    assert type(clean) is PolicyObservationSample
    assert not isinstance(clean, type(raw))
    assert not ({"actual_x", "actual_y", "actual_speed", "true_eta", "response_delay"}
                & {field.name for field in fields(clean)})
    known = sanitize_config(WorldConfig())
    assert type(known) is PolicyKnownConfig


def test_actuator_delay_feedback_contains_only_registered_telemetry():
    feedback = command_feedback(
        command_id="cmd-1", target_id=2, issued_time=1.0, execution_time=1.2,
        accepted=True, success=False, reason="missed pick window",
    )
    assert isclose(feedback.execution_time - feedback.issued_time, 0.2)
    assert not hasattr(feedback, "response_delay")
    assert feedback.reason_code == "missed"
