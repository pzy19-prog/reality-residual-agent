import json

from rra.cli import _run_bench, _summarize


def test_mae_excludes_unattempted_objects_and_success_denominator_includes_them():
    summary = _summarize(
        [
            {"attempted": 1, "successes": 0, "absolute_error_sum": 0.2, "escalations": 0},
            {"attempted": 0, "successes": 0, "absolute_error_sum": 0.0, "escalations": 1},
        ],
        object_count=12,
    )
    assert summary["success_rate"] == 0.0
    assert summary["mean_abs_error"] == 0.2
    assert summary["attempted"] == 1


def test_benchmark_includes_nominal_and_all_intensity_bands(tmp_path):
    bench = _run_bench([0, 1], tmp_path)
    names = [row["scenario"] for row in bench["rows"]]
    assert names == [
        "nominal", "bias-low", "bias-mid", "bias-high", "drift-low", "drift-mid",
        "drift-high", "moving-low", "moving-mid", "moving-high", "load-low",
        "load-mid", "load-high", "combo",
    ]
    assert bench["seeds"] == [0, 1]
    assert bench["seed_role"] == "dev"
    assert json.loads((tmp_path / "bench.json").read_text())["rows"] == bench["rows"]
