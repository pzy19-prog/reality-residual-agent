# RRA V0 freeze acceptance evidence

## Blind-evaluation audit

The seed-freeze and benchmark-artifact checks are three separate assertions:

1. **Frozen seed file unchanged:** `git diff ff1ac91..HEAD -- config/eval_seeds.json` is empty.
2. **Implementation source frozen before artifact:** for implementation commit `c66b4bf5b35dedbbf102a77c36f4d0d8a1938246` and artifact commit `2418406`, `git diff c66b4bf5b35dedbbf102a77c36f4d0d8a1938246..2418406 -- src/` is empty.
3. **Single final evaluation:** eval was run exactly once, and `bench.json`'s `git_sha` equals `c66b4bf5b35dedbbf102a77c36f4d0d8a1938246`.

The seed-freeze commit is earlier than the implementation commit by design. Therefore, do not require the aggregate source diff from `ff1ac91` to the artifact commit to be empty: implementation changes are expected after the seed-only freeze commit. Assertion 2 measures only the implementation-to-artifact interval, ensuring source did not change after the benchmarked implementation was frozen.

For this run, the frozen seed commit is `ff1ac91`, the implementation commit is `c66b4bf5b35dedbbf102a77c36f4d0d8a1938246`, and the benchmark artifact commit is `2418406`. Eval run count was 1, and `bench.json` records `git_sha=c66b4bf5b35dedbbf102a77c36f4d0d8a1938246` with eval seeds `2000–2099`.
