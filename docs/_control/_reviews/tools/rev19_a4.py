"""A4：输出结构 ID、holdout、frozen context 哈希（新旧两版各跑一次后比对）。"""
import json, sys
from rra.eval import context_v3 as c
from rra.eval.holdout import structural_holdout
try:
    from rra.s2.dsl import STRUCTURE_IDS as ids
except ImportError:
    ids = c.STRUCTURE_IDS
variants = ("NO_TEXT_CONTEXT", "HELPFUL_TEXT_CONTEXT", "IRRELEVANT_TEXT_CONTEXT", "MISLEADING_TEXT_CONTEXT")
ctx = {}
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures
st = composition_structures()
for seed in range(130):
    ix = seed % 19
    cat = st[ix] if ix < len(st) else FAULT_FAMILIES[ix - len(st)]
    for v, rec in c.freeze_episode_contexts(f"ep{seed}", seed, cat).items():
        ctx[f"{seed}:{v}"] = rec.content_sha256
print(json.dumps({"structure_ids": list(ids), "context_v3_ids": list(c.STRUCTURE_IDS),
                  "fault_ids": list(c.FAULT_HYPOTHESIS_IDS), "primitives": list(c.PRIMITIVES),
                  "holdout": structural_holdout(), "ctx": ctx}, sort_keys=True, default=str))
