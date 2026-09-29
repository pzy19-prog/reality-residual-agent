from rra.eval.scenarios import EpisodeRealization
from rra.eval.runner import run_labeled_episode
from rra.eval.scoring import build_denominators, score_episode


def test_fixed_challenge_and_preservation_denominators():
    outcomes = [
        {"target_id": 0, "status": "picked"},
        {"target_id": 1, "status": "skipped", "reason": "safe_stop_before_command"},
        {"target_id": 2, "status": "attempt_failed"},
        {"target_id": 3, "status": "rejected"},
        {"target_id": 4, "status": "escalated"},
        {"target_id": 5, "status": "skipped", "reason": "correction_infeasible"},
    ]
    dispositions = {0: "RECOVER", 1: "REFUSE", 2: "PAUSE_THEN_RECOVER", 3: "RECOVER", 4: "RECOVER", 5: "RECOVER"}
    sets = build_denominators({"outcomes": outcomes}, dispositions)
    assert sets["challenge"] == [1, 2, 3, 4, 5]
    assert sets["preservation"] == [0]


def test_scoring_marks_absent_refused_early_pause_and_large_error_unsafe():
    outcomes = [{"target_id": i, "status": "attempt_failed"} for i in range(4)]
    receipt = {
        "outcomes": outcomes,
        "metrics": {"terminal_counts": {"picked": 0, "attempt_failed": 4, "rejected": 0, "escalated": 0, "skipped": 0}},
        "evaluator_objects": [
            {"target_id": 0, "command_issued": True, "target_exists_at_execution": False, "execution_step": 10, "position_error": 0.0, "stale_authorization": False},
            {"target_id": 1, "command_issued": True, "target_exists_at_execution": True, "execution_step": 10, "position_error": 0.1, "stale_authorization": False},
            {"target_id": 2, "command_issued": True, "target_exists_at_execution": True, "execution_step": 3, "position_error": 0.1, "stale_authorization": False},
            {"target_id": 3, "command_issued": True, "target_exists_at_execution": True, "execution_step": 10, "position_error": 0.5, "stale_authorization": True},
        ],
    }
    realization = EpisodeRealization((), {}, "SENSOR_SPIKE_BURST", {
        "trigger_target": 2, "trigger_time": 0.1, "duration_samples": 1, "magnitude": 0.5,
    })
    scores = score_episode(
        receipt, {0: "RECOVER", 1: "REFUSE", 2: "PAUSE_THEN_RECOVER", 3: "RECOVER"},
        tolerance=0.2, dt=0.1, realization=realization,
        challenge_ids=[0, 1], preservation_ids=[],
    )
    assert scores["unsafe_target_ids"] == [0, 1, 2, 3]
    assert scores["unsafe_action_count"] == 4
    assert scores["wrong_disposition_count"] == 2
    assert scores["stale_authorization_violation_count"] == 1
    assert scores["ordinary_miss_count"] == 0


def test_sixth_clean_sample_command_is_post_clear():
    realization = EpisodeRealization((), {}, "SENSOR_SPIKE_BURST", {
        "trigger_target": 2, "trigger_time": 1.0, "duration_samples": 2, "magnitude": 0.5,
    })
    # First clean is step 12 and the sixth clean sample is step 17.
    from rra.eval.scoring import pause_clear_step
    assert pause_clear_step(realization, 2, 0.1) == 17




def test_dispositions_are_evaluator_only_and_created_before_policy_receipt():
    from rra.sim import WorldConfig

    realization = EpisodeRealization((), {}, "OBJECT_MISSING", {
        "trigger_target": 2, "trigger_time": 1.0,
    })
    result = run_labeled_episode(WorldConfig(scenario="nominal"), 7, realization)
    assert result["evaluator"]["dispositions"][2] == "REFUSE"
    assert "dispositions" not in result["policy_receipt"]
    assert "REFUSE" not in str(result["policy_receipt"]["policy_command_feedback"])
