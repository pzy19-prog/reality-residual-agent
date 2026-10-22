# B1-corrected vs B3 — dev seeds

Seeds: 130 from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.

| Metric | B3 dev |
|---|---:|
| Recoverable challenge success | 0.0929 (72/775) |
| Correct refusal rate | 0.9919 |
| Wrong disposition | 607 |
| Miss | 91 |
| Unsafe action | 16 |
| Unsafe: fast layer command | 7 |
| Unsafe: S2 authorized | 9 |
| B1-corrected unsafe action (same episodes) | 43 |
| Preservation regression | 8/582 |
| Preservation regression by cause | fault veto 0; S2 authorized action 7; other 1 |
| Authorizations | 215 |

## Operational cost

- System-2 calls: 2051
- Verifier calls: 28714
- Hypotheses proposed: 28714
- LLM calls: 0
- Production pause seconds: 369.607
- Serial / parallel three-seed wall time: 2.409 / 1.284 s
- Full parallel run wall time: 60.304 s with nproc=8

Receipt SHA-256: `64e4c7eca791d4761565cadd11f159659aa731e47534241b583d2497570f04f1`
