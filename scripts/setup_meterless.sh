#!/usr/bin/env bash
# Idempotently vendor Meterless at the pinned commit and install the bridge's Node deps.
# Vendor files are never modified; vendor/ and node_modules/ are gitignored.
set -euo pipefail

PIN="1742dec56a66e58eef9dda2d2b865823758ca8cd"
REPO_URL="https://github.com/meterless/Meterless.git"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRIDGE="$HERE/bridges/meterless"
VENDOR="$BRIDGE/vendor/Meterless"

if [ ! -d "$VENDOR/.git" ]; then
  mkdir -p "$BRIDGE/vendor"
  git clone --quiet "$REPO_URL" "$VENDOR"
fi

head="$(git -C "$VENDOR" rev-parse HEAD)"
if [ "$head" != "$PIN" ]; then
  if ! git -C "$VENDOR" cat-file -e "$PIN^{commit}" 2>/dev/null; then
    git -C "$VENDOR" fetch --quiet origin
  fi
  git -C "$VENDOR" checkout --quiet --detach "$PIN"
fi

head="$(git -C "$VENDOR" rev-parse HEAD)"
if [ "$head" != "$PIN" ]; then
  echo "setup_meterless: vendor HEAD $head != pinned $PIN" >&2
  exit 1
fi
if [ -n "$(git -C "$VENDOR" status --porcelain)" ]; then
  echo "setup_meterless: vendor tree is dirty; refusing to continue" >&2
  exit 1
fi

(cd "$BRIDGE" && npm ci --ignore-scripts --no-audit --no-fund --loglevel=error)
echo "meterless=$head tsx=$("$BRIDGE/node_modules/.bin/tsx" --version | head -1) node=$(node -v)"
