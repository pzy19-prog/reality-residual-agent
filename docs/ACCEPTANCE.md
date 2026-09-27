# V0 repair acceptance evidence

## Blind-evaluation audit

The seed-freeze and benchmark-artifact checks are three separate assertions:

1. **Frozen seed file unchanged:** `git diff 6377fa6..HEAD -- config/eval_seeds.json` is empty.
2. **Implementation source frozen before artifact:** for implementation commit `<impl_sha>` and artifact commit `<artifact_sha>`, `git diff <impl_sha>..<artifact_sha> -- src/` is empty.
3. **Single final evaluation:** eval was run exactly once, and `bench.json`'s `git_sha` equals `<impl_sha>`.

The seed-freeze commit is earlier than the implementation commit by design. Therefore, do not require the aggregate source diff from `6377fa6` to the artifact commit to be empty: implementation changes are expected after the seed-only freeze commit. Assertion 2 measures only the implementation-to-artifact interval, ensuring source did not change after the benchmarked implementation was frozen.

For this run, `<impl_sha>` is `b025bd457ca30172371c9e0e8d4a16db7c634c31` and `<artifact_sha>` is `21b571d`. Eval run count was 1, and `bench.json` records `git_sha=b025bd457ca30172371c9e0e8d4a16db7c634c31`.
