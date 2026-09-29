from pathlib import Path

from rra.eval.holdout import final_eval_v3_prohibition, structural_holdout


def test_mechanical_holdout_is_preregistered_index_five():
    receipt = structural_holdout()
    assert receipt["holdout_index"] == 5
    assert receipt["holdout_id"] == "AND(SPEED_STEP,ACTUATOR_DELAY)"
    assert len(receipt["pre_exclusion_candidates"]) == 10
    assert len(receipt["eligible_ordered_candidates"]) == 9


def test_final_eval_v3_seed_realization_is_absent():
    receipt = final_eval_v3_prohibition(Path.cwd())
    assert receipt["forbidden_seed_file_exists"] is False
    assert receipt["tracked_equivalent_seed_paths"] == []
    assert receipt["final_eval_v3_seed_values_created"] is False
    assert receipt["final_eval_v3_seed_values_inspected"] is False
