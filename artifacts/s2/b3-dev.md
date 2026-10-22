# B1-corrected vs B3 — dev seeds

Seeds: 130 from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.

| Metric | B3 dev |
|---|---:|
| Recoverable challenge success | 0.0774 (60/775) |
| Correct refusal rate | 1.0000 |
| Wrong disposition | 603 |
| Miss | 104 |
| Unsafe action | 9 |
| Preservation regression | 0/582 |
| Authorizations | 126 |

## Operational cost

- System-2 calls: 5998
- Verifier calls: 83972
- Hypotheses proposed: 83972
- LLM calls: 0
- Production pause seconds: 4855.404
- Serial / parallel three-seed wall time: 0.494 / 0.213 s
- Full parallel run wall time: 956.541 s with nproc=8

Receipt SHA-256: `f90aaf46e54766030247c4541dd327102520976a3e769b8ff801ca1ad515236e`
