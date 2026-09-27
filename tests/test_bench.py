from rra.cli import run_bench


def test_benchmark_uses_fixed_eval_seeds_and_reports_at_least_three_single_scenario_gains(tmp_path):
    bench = run_bench(tmp_path)
    assert bench["eval_seeds"] == list(range(100, 130))
    assert bench["tune_seeds"] == list(range(10))
    gains = sum(row["delta_success_rate"] > 0 for row in bench["rows"] if row["scenario"] != "combo")
    assert gains >= 3
    assert (tmp_path / "bench.json").exists()
