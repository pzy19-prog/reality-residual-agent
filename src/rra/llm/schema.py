"""Provider constrained-output schema for registered B4 proposals."""
from rra.s2.dsl import STRUCTURE_IDS, FaultHypothesis


PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {"type": "string", "enum": [
                        *STRUCTURE_IDS, *(fault.value for fault in FaultHypothesis),
                    ]},
                    "rationale": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["hypothesis_id", "rationale", "evidence_refs"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["items"],
    "additionalProperties": False,
}
