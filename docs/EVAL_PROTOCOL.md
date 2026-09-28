# Evaluation protocol

| Set | Seeds | Status | Use |
|---|---|---|---|
| dev | 0–129 (`config/dev_seeds.json`) | open | All development, diagnosis and tuning |
| eval v1 | 1000–1099 (`config/eval_seeds.json`) | **BURNED** | Published before the V0 repairs and affected by the horizon bug; historical only, never cited as evidence |
| eval v2 | 2000–2099 (`config/eval_seeds_v2.json`) | used once | Frozen in `ff1ac91`; run exactly once on implementation `c66b4bf`; artifact `2418406` |

Rules:
1. Eval seeds are frozen in their own commit before the implementation they measure.
2. No code or threshold changes between the implementation commit and the artifact commit (`git diff <impl>..<artifact> -- src/` is empty).
3. Each eval set is run once. Results are recorded as-is; no changes are made in response to eval results.
4. Hackathon-period evaluation (System-2) will use a new frozen set declared in the same way.
