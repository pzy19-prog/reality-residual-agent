"""PR19 审查：在 d54faa7（主库 checkout，只读）上跑首 20 seed 的 B3 决策，用作独立基准。"""
import json, sys
from pathlib import Path

SCR = Path(sys.argv[1]); MAIN = Path(sys.argv[2])
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.evidence import run_episode

seeds = json.loads((MAIN / "config/dev_seeds.json").read_text())["seeds"]
cfg = v3_world_config("nominal"); st = composition_structures()
dec = {}
for i, seed in enumerate(seeds[:20]):
    ix = i % 19
    real = realize_episode(seed, st[ix]) if ix < len(st) else realize_episode(seed, (), FAULT_FAMILIES[ix - len(st)])
    dec[seed] = run_episode(cfg, seed, True, terminal_monitoring="corrected", realization=real, system2_enabled=True).get("system2_decisions", [])
(SCR / "dec20_old.json").write_text(json.dumps(dec))
print("old rows", sum(len(v) for v in dec.values()))
