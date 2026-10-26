# Reproducing the registered eval-v3 rows

This procedure is for a future reproduction of the existing registered results. It was not run as part of the README release task. Use the formal result commit `dce9e802b024943cb21b8cdb621bdad34187dd73`, not maintained `main`. The implementation freeze tag resolves to `2365a2204ae68354809b99a161fe963b978dbb5d`. The guard checks the tag, tracked changes, new paths, and the registered seed lock; later maintenance paths are rejected by design.

## Prepare an isolated checkout

Fetch repository history and the freeze tag, then create a detached worktree at the exact registered result commit:

```bash
git clone https://github.com/pzy19-prog/reality-residual-agent.git rra-repro
cd rra-repro
git fetch --tags origin
git worktree add --detach ../rra-eval-v3 dce9e802b024943cb21b8cdb621bdad34187dd73
cd ../rra-eval-v3
git rev-parse HEAD
git rev-parse 'impl-freeze-v3^{commit}'
git status --short --branch
```

The first hash must be `dce9e802b024943cb21b8cdb621bdad34187dd73`; the freeze tag must resolve to `2365a2204ae68354809b99a161fe963b978dbb5d`. Create a fresh Python 3.12 environment and install the repository requirements. For offline dependency setup, provide a local wheel directory with all pinned/transitive wheels:

```bash
/usr/bin/python3.12 -m venv .venv
.venv/bin/pip install --no-index --find-links /path/to/wheelhouse -r requirements.txt
```

Run the commands below from the root of the `rra-eval-v3` checkout (`pwd` should end in `rra-eval-v3`). The documented baseline is the original scored result commit; `impl-freeze-v3` names the earlier implementation freeze.

## Offline replay

The runner reads the registered seed file itself; do not edit or substitute it. Run the pure baseline rows and the cached B4 response replay with an output directory outside the worktree. `--replay` consumes saved response/cache records and does not make a live NIM request. Do not pass `--live`.

```bash
OUT=/tmp/rra-eval-v3-replay
mkdir -p "$OUT"
PYTHONPATH=src .venv/bin/python ./rra eval-v3 b1b3 --freeze-tag impl-freeze-v3 --replay --output-dir "$OUT"
PYTHONPATH=src .venv/bin/python ./rra eval-v3 b2 --freeze-tag impl-freeze-v3 --replay --output-dir "$OUT"
PYTHONPATH=src .venv/bin/python ./rra eval-v3 b1-legacy --freeze-tag impl-freeze-v3 --replay --output-dir "$OUT"
PYTHONPATH=src .venv/bin/python ./rra eval-v3 b4 --freeze-tag impl-freeze-v3 --replay --output-dir "$OUT"
```

The CLI will fail closed if the freeze guard, saved replay provenance, or output constraints do not match. The normal row receipts and Markdown reports go to `$OUT`, outside the checkout.

The optional built-in `--replay-check` has a separate side effect: it writes `<checkout>/artifacts/eval_v3/b4_replay_check.json` regardless of `--output-dir`, and can overwrite that path in the checkout. If you need this check, run it only in a disposable reproduction worktree and inspect the resulting diff; do not assume `$OUT` contains every output. For example:

```bash
PYTHONPATH=src .venv/bin/python ./rra eval-v3 b4 --freeze-tag impl-freeze-v3 --replay --replay-check --output-dir "$OUT"
git status --short -- artifacts/eval_v3/b4_replay_check.json
```

The registered runner's bitwise reproducibility is a property of that runner and recorded inputs; portability to a different machine or runtime does not promise identical artifact hashes. For committed metrics and audited field definitions, use the links in the [English README](../README.en.md#formal-eval-v3-results).
