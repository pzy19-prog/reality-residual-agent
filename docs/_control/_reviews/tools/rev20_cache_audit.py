"""PR20 审查：llm_cache 审计（只读）。顶层键、密钥模式、finish_reason、INVALID 原因分布。
用法：PYTHONPATH=<review>/src $PY -B rev20_cache_audit.py <review_root>
"""
import json, re, sys
from collections import Counter
from pathlib import Path

REV = Path(sys.argv[1])
from rra.llm.adapter import HypothesisProposer

class Fixed:
    def __init__(self, resp): self.resp = resp
    def complete(self, body): return self.resp

SECRET = re.compile(r"nvapi-[A-Za-z0-9_-]{10,}|Bearer\s+[A-Za-z0-9._-]{20,}|sk-[A-Za-z0-9]{20,}|\"(authorization|api[_-]?key)\"\s*:", re.I)
files = sorted((REV / "artifacts/llm_cache").glob("*.json"))
keys = Counter(); finish = Counter(); errs = Counter(); hits = []
for f in files:
    text = f.read_text(encoding="utf-8")
    if SECRET.search(text): hits.append(f.name)
    rec = json.loads(text)
    keys[tuple(sorted(rec))] += 1
    resp = rec.get("response", {})
    try: finish[resp["choices"][0].get("finish_reason")] += 1
    except Exception: finish["<no choices>"] += 1
    p = HypothesisProposer(Fixed(resp)).propose({}, "")
    errs[(p.error or "OK")[:90]] += 1
art_hits = [str(p.relative_to(REV)) for p in (REV / "artifacts").rglob("*.json")
            if "llm_cache" not in p.parts and SECRET.search(p.read_text(encoding="utf-8", errors="ignore"))]
print(json.dumps({"cache_files": len(files), "top_level_keys": {"|".join(k): n for k, n in keys.items()},
                  "secret_hits_cache": hits, "secret_hits_other_artifacts": art_hits,
                  "finish_reason": dict(finish), "parse_result_top": errs.most_common(12)},
                 indent=1, ensure_ascii=False))
