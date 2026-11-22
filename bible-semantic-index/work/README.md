# BSI working state: immutable private snapshots

**Public repository policy:** this directory contains **only the procedure,
schema and tracked editorial inputs**, never source-derived complete private
word-witness archives. Do NOT commit generated `index.json` files from private
audits, UBS dictionary prose, MACULA linguistic annotations or ZIPs here.

## The three actual working states

| Stream | Complete internal state included | Source-pinned workflow |
| --- | --- | --- |
| `entity` | Complete ACAI-derived internal entity `index.json`, reduced keyterm-free projection, minimal English labels | [Entity index](../../.github/workflows/entity-index.yml) |
| `ubs-greek` | Full **137,741-original-word** source-evidence candidate index, plus 2,728 private sense-context review batches | [UBS Greek](../../.github/workflows/bsi-ubs-greek.yml) |
| `ubs-hebrew` | Source-reviewed final 275-additional-word lexical candidate, full 53,981-candidate semantic feasibility audit, and the complete private 72-token source-context pilot | [UBS Hebrew](../../.github/workflows/bsi-ubs-hebrew.yml) |

The committed dictionary `links/dictionaries/*/index.json` files are
**source baselines**, and public GitHub Releases hold only approved
redistributable editions. These snapshots are a **different, private
working layer**. Stored source-revision locks and the exact producing
`Bible-Resources` commit make every snapshot reproducible.

## Permanent storage

The archive script creates one **content-verified, deterministic**
`bsi-work-<stream>-<40-character-commit>.tar.gz` containing precisely
the allowed complete working inputs and a `manifest.json`. Separate
`.tar.gz.sha256` and `.tar.gz.manifest.json` assets repeat the
checksums, source revisions, original producing Git commit, private
editorial status and non-publication boundary.

For every **successful protected-main push or main-branch manual dispatch** of the corresponding BSI
workflow, if the private destination is configured, the workflow:

1. Rebuilds and source-validates the unchanged canonical index.
2. Packs only the explicit complete working fields; checks schemas,
   original word counts and source commit, hash and private status.
3. Confirms the destination repository is *actually private* using GitHub
   API. An unset token, public repository or failed permission check
   **never** falls back to a public release, public branch or Actions
   artifact.
4. Writes an **immutable private GitHub Release** tagged
   `bsi-work-<stream>-<full-commit>`; downloads the three assets back
   and byte-compares. Existing tags must have identical bytes or the
   workflow fails (no silent overwrite).

The original 14-day Actions artifacts remain **temporary** and cannot
be treated as durable storage. A green source-validation job with the
`NOT saved durably` warning is **not archival success**.

### One-time setup required

The owner must provision a **dedicated private GitHub repository**, not
`icfmp/Bible-Resources` (which is public), and configure in
`icfmp/Bible-Resources` settings:

- Repository **variable** `BSI_PRIVATE_SNAPSHOT_REPO` =
  `OWNER/PRIVATE-REPOSITORY`.
- Repository **secret** `BSI_PRIVATE_SNAPSHOT_TOKEN` = fine-grained token
  with **Contents: read/write** on **that private repository only**.
  No token or private source fields belong in a committed file.
- The private destination needs a default branch. Access should be
  restricted to project custodians; do not share release URLs publicly.

**Until both settings and the private repository exist, there are
no durable working-state snapshots.** No backup is claimed by merely
committing this workflow or its documentation.

Once configured, run each source-pinned BSI workflow via GitHub Actions
**Run workflow**, selecting **main**. On a verified main-branch
`workflow_dispatch`, the same privacy/reproducibility checks apply and
an immutable private snapshot is saved. Never dispatch a branch-based
source candidate and expect it to be archived. You can rebuild any one of
the three streams without creating artificial Git history commits.

## Recover an exact historical working state

Using private repository access (never print the token):

```bash
# Example: replace placeholders with the real stream, full source SHA,
# and your private destination repository.
tag="bsi-work-ubs-greek-<40-char-source-commit>"
gh release download "$tag" \
  --repo "OWNER/PRIVATE-REPOSITORY" --dir ./private-bsi-recovery
cd private-bsi-recovery
sha256sum --check "bsi-work-ubs-greek-<40-char-source-commit>.tar.gz.sha256"
python3 -I ../bible-semantic-index/scripts/work_snapshot.py verify \
  --archive "bsi-work-ubs-greek-<40-char-source-commit>.tar.gz"
mkdir -p restored
tar -xzf "bsi-work-ubs-greek-<40-char-source-commit>.tar.gz" -C restored
```

Read `restored/manifest.json` first; its source revisions and exact
producing commit must be checked out before continuing editorial work.
The JSON evidence files are **not** semantic sense approvals and must
never be directly substituted for a published crosswalk. New editorial
decisions should be committed as independent, source-justified and
reversible data inputs, then used in a new reproducible snapshot.

## Limits

This implementation supplies the **archive format, integrity verification,
private-only upload, read-back verification and recovery contract**.
It does not provision a private repository or create GitHub secrets on
your behalf. GitHub Release history is persistent but not independently
backed up: retain a separate owner-controlled encrypted backup if data
loss resilience beyond one provider is required.
