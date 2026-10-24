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

- System-2 calls: 1975
- Verifier calls: 27650
- Hypotheses proposed: 27650
- LLM calls: 0
- Production pause seconds: 401.558
- Serial / parallel three-seed wall time: 2.682 / 1.376 s
- Full parallel run wall time: 68.292 s with nproc=8

Receipt SHA-256: `aba2100d800ef522cde064f228ec5aae1a247493489f0aca0e597f9e03dd3704`
