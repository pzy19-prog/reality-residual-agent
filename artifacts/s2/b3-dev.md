# B1-corrected vs B3 — dev seeds

Seeds: 130 from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.

| Metric | B3 dev |
|---|---:|
| Recoverable challenge success | 0.1084 (84/775) |
| Correct refusal rate | 0.8871 |
| Wrong disposition | 603 |
| Miss | 96 |
| Unsafe action | 21 |
| Unsafe: fast layer command | 17 |
| Unsafe: S2 authorized | 4 |
| B1-corrected unsafe action (same episodes) | 43 |
| Preservation regression | 0/582 |
| Preservation regression by cause | fault veto 0; S2 authorized action 0; other 0 |
| Authorizations | 220 |

## Operational cost

- System-2 calls: 2045
- Verifier calls: 28630
- Hypotheses proposed: 28630
- LLM calls: 0
- Production pause seconds: 400.055
- Serial / parallel three-seed wall time: 2.623 / 1.280 s
- Full parallel run wall time: 66.329 s with nproc=8

Receipt SHA-256: `c8ad4d91fde6a7c04ae4c2a64abecfb2be487c7a30e1d2ef4a01f35c97faa949`
