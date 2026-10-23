# B1-corrected vs B3 — dev seeds

Seeds: 130 from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.

| Metric | B3 dev |
|---|---:|
| Recoverable challenge success | 0.1084 (84/775) |
| Correct refusal rate | 1.0000 |
| Wrong disposition | 589 |
| Miss | 96 |
| Unsafe action | 7 |
| Unsafe: fast layer command | 7 |
| Unsafe: S2 authorized | 0 |
| B1-corrected unsafe action (same episodes) | 43 |
| Preservation regression | 0/582 |
| Preservation regression by cause | fault veto 0; S2 authorized action 0; other 0 |
| Authorizations | 209 |

## Operational cost

- System-2 calls: 1961
- Verifier calls: 27454
- Hypotheses proposed: 27454
- LLM calls: 0
- Production pause seconds: 386.475
- Serial / parallel three-seed wall time: 2.722 / 1.359 s
- Full parallel run wall time: 64.394 s with nproc=8

Receipt SHA-256: `2bcf3aa81be5d7a7b77d14c29c14c3d0016c072346bffc495d52be5a3c2f5092`
