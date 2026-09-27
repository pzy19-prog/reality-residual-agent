# Open Agent Hackathon 2026 — V0 pre-hackathon baseline

All components listed below are declared as existing before the hackathon implementation period. They form the complete V0 baseline; V0 has no LLM integration.

- Seeded 2D conveyor world with nominal operation, low/mid/high position bias, linear drift, moving-target speed delta, load speed step, and the unchanged combined-disturbance case. Scenario values live in `config/scenarios.json`.
- Nominal scripted pick planner.
- Sliding-window residual monitor and heuristic disturbance classifier.
- EWMA residual estimator with bounded timing correction and fixed fail-closed safety threshold.
- Deterministic controller with speed, position, and pick-window limits.
- JSON episode receipts, same-seed compensation on/off benchmark, CLI, Dockerfile, tests, and project documentation.

The V0 repair benchmark uses development seeds `0–129` and a separately frozen blind evaluation set `1000–1099` (`freeze blind eval seeds`). Success rate divides successful picks by all generated objects; unattempted objects after an escalation count as failures. MAE is the aggregate pick-window error over attempted picks only. The combo fast rule layer escalates in every episode and fails closed; handling that state is a hackathon System-2 objective.

Final frozen eval result (100 seeds): nominal success was `0.986` with and without compensation; all four low-disturbance off success rates were greater than zero. Combo success was `0.000` off and `0.003` on, with 100 escalations in each mode. The complete scenario table is in `README.md` and the raw artifact is `bench.json`.

This statement records the project baseline as pre-hackathon work for the applicable rules 4.2 and 5.2. It does not claim hackathon judging eligibility or acceptance beyond that declaration.
