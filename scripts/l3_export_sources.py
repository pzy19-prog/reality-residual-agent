#!/usr/bin/env python3
"""Export the preregistered 20-episode L3 source tables."""
import json
from pathlib import Path

from rra.evidence.sources import export_sources

root = Path(__file__).resolve().parents[1]
out = root / "outputs/l3/sources"
result = export_sources(out, 20)
audit = root / "outputs/l3/reference-audit.json"
audit.write_text(json.dumps(result["audits"], sort_keys=True, indent=2), encoding="utf-8")
print(f"episodes={len(result['audits'])} decision_points={sum(x['decision_points'] for x in result['audits'])}")
