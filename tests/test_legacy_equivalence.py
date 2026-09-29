from rra.eval.legacy_anchor import assert_legacy_anchor, build_legacy_anchor


def test_sanitized_path_matches_repair04_anchor():
    assert_legacy_anchor(build_legacy_anchor())
