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

- System-2 calls: 2010
- Verifier calls: 28140
- Hypotheses proposed: 28140
- LLM calls: 0
- Production pause seconds: 825.221
- Serial / parallel three-seed wall time: 4.901 / 2.774 s
- Full parallel run wall time: 148.087 s with nproc=8

Receipt SHA-256: `bfda4d101bd79f8d62738807402b33e24aba29028f5f4bc550a9b13304cb1132`
