# B1-corrected vs B3 — dev seeds

Seeds: 130 from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.

| Metric | B3 dev |
|---|---:|
| Recoverable challenge success | 0.0374 (29/775) |
| Correct refusal rate | 1.0000 |
| Wrong disposition | 1299 |
| Miss | 16 |
| Unsafe action | 8 |
| Unsafe: fast layer command | 0 |
| Unsafe: S2 authorized | 8 |
| B1-corrected unsafe action (same episodes) | 43 |
| Preservation regression | 577/582 |
| Authorizations | 353 |

## Operational cost

- System-2 calls: 10465
- Verifier calls: 146510
- Hypotheses proposed: 146510
- LLM calls: 0
- Production pause seconds: 1026.369
- Serial / parallel three-seed wall time: 0.632 / 0.279 s
- Full parallel run wall time: 257.351 s with nproc=8

Receipt SHA-256: `72275851ebcf6a64183a3c8c6aa375cbeca9a0a4f2da18d112cba2f878fa80ef`
