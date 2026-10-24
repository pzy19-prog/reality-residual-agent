"""PR19 审查：在 ab509d3 代码上独立复跑 B3 dev（A2/A3），输出到 scratch，不写仓库。"""
import json, subprocess, sys
from pathlib import Path

SCR = Path(sys.argv[1]); REV = Path(sys.argv[2])
out = SCR / "b3dev_new"; out.mkdir(exist_ok=True)

from rra.eval.b3_dev import run_b3_dev, _run_seed
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.evidence import run_episode

r = run_b3_dev(out, nproc=10)
committed = json.loads((REV / "artifacts/s2/b3-dev.json").read_text())
old = json.loads(subprocess.check_output(["git", "-C", str(REV), "show", "d54faa7:artifacts/s2/b3-dev.json"]))

res = {}
res["repro_receipt_eq_committed"] = r["receipt_sha256"] == committed["receipt_sha256"]
res["repro_receipt"] = r["receipt_sha256"]; res["committed_receipt"] = committed["receipt_sha256"]
res["old_receipt"] = old["receipt_sha256"]
nb = {e["seed"]: e for e in r["episodes"]}; ob = {e["seed"]: e for e in old["episodes"]}
res["b1_hash_eq_old"] = sum(nb[s]["b1_receipt_sha256"] == ob[s]["b1_receipt_sha256"] for s in ob)
res["b3_hash_eq_old"] = sum(nb[s]["b3_receipt_sha256"] == ob[s]["b3_receipt_sha256"] for s in ob)
skip = {"b3_receipt_sha256", "system2_decisions", "pause_seconds"}
diff_fields = {}
for s in ob:
    for k in set(ob[s]) | set(nb[s]):
        if k in skip: continue
        if ob[s].get(k) != nb[s].get(k): diff_fields.setdefault(k, []).append(s)
res["episode_field_diffs_vs_old(excl b3 hash/decisions)"] = {k: len(v) for k, v in diff_fields.items()}
res["metrics_eq_old"] = r["metrics"] == old["metrics"]
res["seed_count"] = len(ob)

# A3：首 20 seed 诊断开关
seeds = json.loads((REV / "config/dev_seeds.json").read_text())["seeds"]
cfg = v3_world_config("nominal"); st = composition_structures()
tog_hash = tog_dec = 0; dec20 = {}
for i, seed in enumerate(seeds[:20]):
    ix = i % 19
    real = realize_episode(seed, st[ix]) if ix < len(st) else realize_episode(seed, (), FAULT_FAMILIES[ix - len(st)])
    a = run_episode(cfg, seed, True, terminal_monitoring="corrected", realization=real, system2_enabled=True, include_s2_diagnostics=False)
    b = run_episode(cfg, seed, True, terminal_monitoring="corrected", realization=real, system2_enabled=True, include_s2_diagnostics=True)
    tog_hash += a["receipt_sha256"] == b["receipt_sha256"]
    tog_dec += a.get("system2_decisions") == b.get("system2_decisions")
    dec20[seed] = a.get("system2_decisions", [])
    assert "actual_x_at_execution" not in json.dumps(b["evaluator_objects"])
res["a3_toggle_hash_eq"] = tog_hash; res["a3_toggle_dec_eq"] = tog_dec
res["a3_dec_eq_committed"] = sum(dec20[s] == {e["seed"]: e for e in committed["episodes"]}[s].get("system2_decisions") for s in dec20)
res["a3_decision_rows"] = sum(len(v) for v in dec20.values())
(SCR / "dec20_new.json").write_text(json.dumps(dec20))
print(json.dumps(res, indent=1))
