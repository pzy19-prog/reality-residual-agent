import json, sys
from pathlib import Path
REV = Path(sys.argv[1]); OUT = Path(sys.argv[2])
import rra; print("rra.__file__", rra.__file__)
from rra.eval.b4_dev import _realization, _ReadThroughProvider, _MemoizedProposer
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
all_seeds = json.loads((REV / "config/dev_seeds.json").read_text())["seeds"]
seeds = json.loads((REV / "artifacts/s2/diag-d1g.json").read_text())["seeds"]
idx = {s: i for i, s in enumerate(all_seeds)}
cfg = v3_world_config("nominal"); cache = REV / "artifacts/llm_cache"
res = {}
for seed in seeds:
    real = _realization(idx[seed], seed)
    ctx = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)
    for v in VARIANTS:
        prop = _MemoizedProposer(HypothesisProposer(_ReadThroughProvider(cache, replay_only=True)))
        for mode in ("B4_STRICT", "B4_TIEBREAK"):
            r = run_episode(cfg, seed, True, terminal_monitoring="corrected", realization=real,
                            text_context=ctx[v].text, system2_enabled=True, s2_variant=mode, proposer=prop)
            res[f"{seed}|{v}|{mode}"] = {"decisions": r["system2_decisions"],
                "action": [d.get("action") for d in r["system2_decisions"]],
                "authorization": [d.get("authorization") for d in r["system2_decisions"]],
                "gate_reason": [d.get("gate_reason") for d in r["system2_decisions"]]}
OUT.write_text(json.dumps(res, sort_keys=True, default=str))
print("keys", len(res), "seeds", len(seeds), "variants", list(VARIANTS))
