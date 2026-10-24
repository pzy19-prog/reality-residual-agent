"""PR20 审查：D4 语义审计（离线回放，只读）。
统计每个 TEXT_TIEBREAK 决策：被选结构之前是否排着 fault ID；该 proposal 是否含未知 ID。
用法：PYTHONPATH=<review>/src $PY -B rev20_d4_audit.py <review_root> <out_json>
"""
import json, sys
from pathlib import Path

REV = Path(sys.argv[1]); OUT = Path(sys.argv[2])
from rra.eval.b4_dev import _realization, _ReadThroughProvider, _MemoizedProposer
from rra.eval.context_v3 import VARIANTS, freeze_episode_contexts
from rra.eval.framework import v3_world_config
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer, FAULT_HYPOTHESIS_IDS

all_seeds = json.loads((REV / "config/dev_seeds.json").read_text())["seeds"]
seeds = json.loads((REV / "artifacts/s2/diag-d1g.json").read_text())["seeds"]
idx = {s: i for i, s in enumerate(all_seeds)}
cfg = v3_world_config("nominal"); cache = REV / "artifacts/llm_cache"
faults = set(FAULT_HYPOTHESIS_IDS)
res = {v: {"text_tiebreak": 0, "fault_before_selected": 0, "unknown_ids_present": 0,
           "first_is_fault": 0, "proposals_valid": 0, "selected_not_first": 0,
           "tiebreak_authorized": 0, "affected_authorized": 0, "examples": []} for v in VARIANTS}
for seed in seeds:
    real = _realization(idx[seed], seed)
    ctx = freeze_episode_contexts(str(seed), seed, real.fault_family or real.structure)
    for v in VARIANTS:
        prop = _MemoizedProposer(HypothesisProposer(_ReadThroughProvider(cache, replay_only=True)))
        tie = run_episode(cfg, seed, True, terminal_monitoring="corrected", realization=real,
                          text_context=ctx[v].text, system2_enabled=True,
                          s2_variant="B4_TIEBREAK", proposer=prop)
        ranks = {(int(p["target_id"]), p["time"]): p for p in tie.get("system2_proposal_rank", [])}
        r = res[v]
        for p in ranks.values():
            if not p["error"]:
                r["proposals_valid"] += 1
                if p["ranked_ids"] and p["ranked_ids"][0] in faults:
                    r["first_is_fault"] += 1
        for d in tie["system2_decisions"]:
            if d.get("gate_reason") != "TEXT_TIEBREAK":
                continue
            r["text_tiebreak"] += 1
            p = ranks.get((int(d["target_id"]), d["time"]), {})
            sel = d.get("tiebreak_selected_structure_id")
            ids = p.get("ranked_ids", [])
            pos = ids.index(sel) if sel in ids else None
            fb = pos is not None and any(x in faults for x in ids[:pos])
            unk = bool(p.get("unknown_ids"))
            r["fault_before_selected"] += fb
            r["unknown_ids_present"] += unk
            r["selected_not_first"] += pos not in (0, None)
            authd = d.get("authorization") is not None
            r["tiebreak_authorized"] += authd
            r["affected_authorized"] += authd and (fb or unk)
            if (fb or unk) and len(r["examples"]) < 5:
                r["examples"].append({"seed": seed, "target": d["target_id"], "time": d["time"],
                                      "ranked_ids": ids, "unknown_ids": p.get("unknown_ids"),
                                      "selected": sel, "authorized": authd})
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps({v: {k: x for k, x in r.items() if k != "examples"} for v, r in res.items()}, indent=1))
