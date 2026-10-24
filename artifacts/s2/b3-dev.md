# B1-corrected vs B3 — dev seeds

Seeds: 130 from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.

| Metric | B3 dev |
|---|---:|
| Recoverable challenge success | 0.1084 (84/775) |
| Correct refusal rate | 1.0000 |
| Wrong disposition | 588 |
| Miss | 97 |
| Unsafe action | 7 |
| Unsafe: fast layer command | 7 |
| Unsafe: S2 authorized | 0 |
| B1-corrected unsafe action (same episodes) | 43 |
| Preservation regression | 0/582 |
| Preservation regression by cause | fault veto 0; S2 authorized action 0; other 0 |
| Authorizations | 210 |

## Operational cost

- System-2 calls: 2009
- Verifier calls: 28126
- Hypotheses proposed: 28126
- LLM calls: 0
- Production pause seconds: 503.707
- Serial / parallel three-seed wall time: 2.806 / 1.473 s
- Full parallel run wall time: 91.493 s with nproc=8

Receipt SHA-256: `75115f44cc3bd212bd461620bd8c8a5a4e8f310a2e8e5823edf1136bd90a5e32`
