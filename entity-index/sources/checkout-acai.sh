#!/usr/bin/env bash
# Obtain the frozen original ACAI witness without changing its content.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="$ROOT/entity-index/sources/checkouts/acai"
REV="e80a874e8282f996199c595378a3b3b9a43aac22"
if [[ ! -d "$DEST/.git" ]]; then
  mkdir -p "$(dirname "$DEST")"
  git clone https://github.com/icfmp/ACAI.git "$DEST"
fi
if [[ -n "$(git -C "$DEST" status --porcelain --untracked-files=all)" ]]; then
  echo "Refusing dirty original-source checkout at $DEST" >&2
  exit 1
fi
git -C "$DEST" fetch --quiet origin "$REV"
git -C "$DEST" checkout --detach --quiet "$REV"
test "$(git -C "$DEST" rev-parse HEAD)" = "$REV"
echo "Frozen ACAI source ready: $DEST ($REV)"
