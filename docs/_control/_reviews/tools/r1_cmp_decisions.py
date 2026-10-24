import json, sys
from collections import Counter
S=sys.argv[1]
o=json.load(open(f"{S}/old_dec.json")); n=json.load(open(f"{S}/new_dec.json"))
print("keys old/new", len(o), len(n), "same keyset", o.keys()==n.keys())
print("(a) total decisions old", sum(len(v["decisions"]) for v in o.values()), "new", sum(len(v["decisions"]) for v in n.values()))
print("   per-key count mismatch", sum(len(o[k]["decisions"])!=len(n[k]["decisions"]) for k in o))
print("(b) action seq equal", sum(o[k]["action"]==n[k]["action"] for k in o), "/", len(o))
print("    authorization seq equal", sum(o[k]["authorization"]==n[k]["authorization"] for k in o), "/", len(o))
print("    both equal", sum(o[k]["action"]==n[k]["action"] and o[k]["authorization"]==n[k]["authorization"] for k in o), "/", len(o))
for m in ("B4_STRICT","B4_TIEBREAK"):
    ks=[k for k in o if k.endswith(m)]
    print("    ",m,"both equal",sum(o[k]["action"]==n[k]["action"] and o[k]["authorization"]==n[k]["authorization"] for k in ks),"/",len(ks))
diff_other=0; diff_fields=Counter(); gr=Counter(); tot=0
for k in o:
    if len(o[k]["decisions"])!=len(n[k]["decisions"]): continue
    for a,b in zip(o[k]["decisions"],n[k]["decisions"]):
        tot+=1
        fs=[f for f in set(a)|set(b) if f!="gate_reason" and a.get(f)!=b.get(f)]
        if fs: diff_other+=1; diff_fields.update(fs)
        if a.get("gate_reason")!=b.get("gate_reason"): gr[(a.get("gate_reason"),b.get("gate_reason"))]+=1
print("(c) decisions compared",tot,"with non-gate_reason field differences",diff_other, dict(diff_fields))
print("(d) gate_reason changes old->new:")
for (a,b),c in gr.most_common(): print("   ",a,"->",b,c)
print("NEW B4_TIEBREAK gate_reason Counter:")
c=Counter(g for k in n if k.endswith("B4_TIEBREAK") for g in n[k]["gate_reason"])
for g,x in c.most_common(): print("   ",g,x)
print("NEW B4_STRICT gate_reason Counter:", Counter(g for k in n if k.endswith("B4_STRICT") for g in n[k]["gate_reason"]).most_common())
print("NEW auth non-null & gate_reason==TEXT_TIEBREAK:", sum(1 for k in n for d in n[k]["decisions"] if d.get("authorization") is not None and d.get("gate_reason")=="TEXT_TIEBREAK"))
print("NEW gate_reason==TEXT_TIEBREAK total:", sum(1 for k in n for d in n[k]["decisions"] if d.get("gate_reason")=="TEXT_TIEBREAK"))
print("OLD B4_TIEBREAK gate_reason Counter:", Counter(g for k in o if k.endswith("B4_TIEBREAK") for g in o[k]["gate_reason"]).most_common())
