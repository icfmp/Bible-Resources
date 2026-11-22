#!/usr/bin/env bash
# Store a verified BSI work archive as an immutable release in a PRIVATE repo.
# Requires GH_TOKEN scoped ONLY to the private destination and contents:write.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: publish_private_work_snapshot.sh SNAPSHOT.tar.gz SOURCE_COMMIT" >&2
  exit 2
fi
archive="$1"
commit="$2"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]] || [[ ! -f "$archive" ]]; then
  echo "Invalid pinned commit or archive" >&2
  exit 2
fi

# An empty configuration is not a successful backup. Exit separately so
# callers can log an explicit warning and publish nothing.
if [[ -z "${BSI_PRIVATE_SNAPSHOT_REPO:-}" || -z "${GH_TOKEN:-}" ]]; then
  echo "::warning::BSI private work snapshot NOT archived: configure BSI_PRIVATE_SNAPSHOT_REPO and BSI_PRIVATE_SNAPSHOT_TOKEN."
  exit 78
fi

if [[ ! "$BSI_PRIVATE_SNAPSHOT_REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo "::error::Invalid private repository owner/name" >&2
  exit 2
fi

python3 -I bible-semantic-index/scripts/work_snapshot.py verify --archive "$archive"
basename="$(basename "$archive")"
[[ "$basename" =~ ^bsi-work-(entity|ubs-greek|ubs-hebrew)-([0-9a-f]{40})\.tar\.gz$ ]] ||
  { echo "::error::Unexpected archive name" >&2; exit 2; }
[[ "${BASH_REMATCH[2]}" == "$commit" ]] ||
  { echo "::error::Source commit differs from archive" >&2; exit 2; }

# The destination is always independently verified PRIVATE before upload.
# Never fall back to the public repository, public release or Actions cache.
private="$(gh api "repos/$BSI_PRIVATE_SNAPSHOT_REPO" --jq '.private')"
if [[ "$private" != "true" ]]; then
  echo "::error::Refusing work-snapshot upload: destination is NOT a private GitHub repository" >&2
  exit 1
fi
default_branch="$(gh api "repos/$BSI_PRIVATE_SNAPSHOT_REPO" --jq '.default_branch')"
[[ -n "$default_branch" ]] || { echo "::error::Missing private repo default branch" >&2; exit 1; }

tag="${basename%.tar.gz}"
sha_file="${archive}.sha256"
manifest_file="${archive}.manifest.json"

# Release names are source-commit-bound and never rewritten. Verify an
# existing release rather than pretending to have persisted a newer version.
if gh release view "$tag" --repo "$BSI_PRIVATE_SNAPSHOT_REPO" >/dev/null 2>&1; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  gh release download "$tag" --repo "$BSI_PRIVATE_SNAPSHOT_REPO" \
    --pattern "$basename" \
    --pattern "${basename}.sha256" \
    --pattern "${basename}.manifest.json" \
    --dir "$tmp"
  cmp "$archive" "$tmp/$basename"
  cmp "$sha_file" "$tmp/${basename}.sha256"
  cmp "$manifest_file" "$tmp/${basename}.manifest.json"
  echo "PRIVATE_BSI_SNAPSHOT_ALREADY_ARCHIVED_VERIFIED $tag"
else
  gh release create "$tag" "$archive" "$sha_file" "$manifest_file" \
    --repo "$BSI_PRIVATE_SNAPSHOT_REPO" \
    --target "$default_branch" \
    --title "BSI private working snapshot: $tag" \
    --notes "INTERNAL WORKING SOURCE EVIDENCE ONLY. Not approved for publication or semantic assertions. Exact source commit: $commit. Do not copy these release assets to a public repository."
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  gh release download "$tag" --repo "$BSI_PRIVATE_SNAPSHOT_REPO" \
    --pattern "$basename" \
    --pattern "${basename}.sha256" \
    --pattern "${basename}.manifest.json" \
    --dir "$tmp"
  cmp "$archive" "$tmp/$basename"
  cmp "$sha_file" "$tmp/${basename}.sha256"
  cmp "$manifest_file" "$tmp/${basename}.manifest.json"
  echo "PRIVATE_BSI_SNAPSHOT_UPLOADED_READBACK_VERIFIED $tag"
fi
