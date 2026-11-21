#!/usr/bin/env bash
# Obtain an exact frozen upstream ACAI witness without editing it.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="$ROOT/bible-semantic-index/sources/checkouts/acai"
LOCK="$ROOT/bible-semantic-index/data/source.lock.json"
readarray -t INFO < <(python3 - "$LOCK" <<'PY'
import json
import sys
from pathlib import Path
lock=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(lock["source_repository"])
print(lock["source_commit"])
PY
)
URL="${INFO[0]}"
REV="${INFO[1]}"
if [[ ! -d "$DEST/.git" ]]; then
  mkdir -p "$(dirname "$DEST")"
  git clone --quiet "$URL" "$DEST"
fi
if [[ -n "$(git -C "$DEST" status --porcelain --untracked-files=all)" ]]; then
  echo "Refusing dirty original-source checkout: $DEST" >&2
  exit 1
fi
git -C "$DEST" fetch --quiet origin "$REV"
git -C "$DEST" checkout --detach --quiet "$REV"
test "$(git -C "$DEST" rev-parse HEAD)" = "$REV"
echo "Frozen ACAI source ready: $DEST ($REV)"
