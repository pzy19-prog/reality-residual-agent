from dataclasses import fields
from math import isclose

from rra.evidence.policy import (
    PolicyCommandFeedback,
    PolicyKnownConfig,
    PolicyObservationSample,
    PolicyTargetPresenceEvent,
    command_feedback,
    sanitize_config,
    sanitize_observation,
)
from rra.sim import World, WorldConfig
from rra.evidence import run_episode
from rra.eval.scenarios import EpisodeRealization
from rra.eval.framework import v3_world_config


def test_policy_schemas_are_exact_whitelists():
    expected = {
        PolicyObservationSample: {
            "target_id", "step", "time", "observed_x", "observed_y",
            "nominal_x", "nominal_y", "nominal_speed",
        },
        PolicyKnownConfig: {"dt", "tolerance", "x_pick", "y_pick", "belt_speed"},
        PolicyTargetPresenceEvent: {"target_id", "step", "time", "target_observed"},
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
    assert not ({"actual_x", "actual_y", "actual_speed", "true_eta", "response_delay", "target_present"}
                & {field.name for field in fields(clean)})
    presence_fields = {field.name for field in fields(PolicyTargetPresenceEvent)}
    assert presence_fields == {"target_id", "step", "time", "target_observed"}
    assert "target_present" not in presence_fields
    known = sanitize_config(WorldConfig())
    assert type(known) is PolicyKnownConfig


def test_actuator_delay_feedback_contains_only_registered_telemetry():
    feedback = command_feedback(
        command_id="cmd-1", target_id=2, issued_time=1.0, execution_time=1.2,
        accepted=True, success=False,
    )
    assert isclose(feedback.execution_time - feedback.issued_time, 0.2)
    assert not hasattr(feedback, "response_delay")
    assert feedback.reason_code == "missed"


def test_runner_feedback_payload_contains_only_whitelisted_fields():
    receipt = run_episode(WorldConfig(scenario="nominal"), 5, True)
    allowed = {field.name for field in fields(PolicyCommandFeedback)}
    assert receipt["policy_command_feedback"]
    assert all(set(row) <= allowed for row in receipt["policy_command_feedback"])
    assert all("response_delay" not in row for row in receipt["policy_command_feedback"])


def test_presence_event_emitted_for_every_normal_sample_and_is_deterministic():
    config = v3_world_config("nominal")
    first = run_episode(config, 12, True, realization=EpisodeRealization((), {}, None, {}))
    second = run_episode(config, 12, True, realization=EpisodeRealization((), {}, None, {}))
    events = first["policy_target_presence_events"]
    assert events == second["policy_target_presence_events"]
    assert len(events) == config.episode_steps * config.object_count
    assert all(event["target_observed"] is True for event in events)
    assert all(set(event) == {"target_id", "step", "time", "target_observed"} for event in events)
    assert "target_present" not in str(events)


def test_object_missing_keeps_false_presence_events_and_stops_position_samples(monkeypatch):
    import rra.evidence.episode as episode_module

    config = v3_world_config("nominal")
    realization = EpisodeRealization((), {}, "OBJECT_MISSING", {
        "trigger_target": 2, "trigger_time": 1.0,
    })
    sanitized_target_steps = []
    original_sanitize = episode_module.sanitize_observation

    def track_sanitized_sample(observation):
        sanitized_target_steps.append((observation.target_id, observation.step))
        return original_sanitize(observation)

    monkeypatch.setattr(episode_module, "sanitize_observation", track_sanitized_sample)
    receipt = run_episode(config, 12, True, realization=realization)
    target_events = [row for row in receipt["policy_target_presence_events"] if row["target_id"] == 2]
    assert [row["target_observed"] for row in target_events[:10]] == [True] * 10
    assert [row["target_observed"] for row in target_events[10:]] == [False] * (config.episode_steps - 10)
    assert len(target_events) == config.episode_steps
    assert all((2, step) in sanitized_target_steps for step in range(10))
    assert all((2, step) not in sanitized_target_steps for step in range(10, config.episode_steps))
    assert all(set(row) == {"target_id", "step", "time", "target_observed"} for row in target_events)
    assert not ({"actual_x", "actual_y", "actual_speed", "fault_family",
                 "evaluator_disposition", "target_present"} & set(target_events[10]))
    assert "target_present" not in str(receipt["policy_target_presence_events"])
