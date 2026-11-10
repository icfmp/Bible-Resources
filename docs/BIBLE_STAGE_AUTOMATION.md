# Run Bible onboarding checks through GitHub Actions

This is the **machine-execution companion** to the
[seven-stage Bible workflow](BIBLE_7_STAGE_WORKFLOW.md).
It is **read-only research**. It does not translate, modify, normalize,
compile, publish, license or approve biblical content.

The repository already contains powerful source/native SWORD inspectors.
`scripts/bible_stage_runner.py` invokes them in a repeatable, bounded
**one-stage-per-workflow-run** arrangement. Source ZIPs remain in the runner's
temporary directory, never in logs, Git artifacts or the published catalogue.

## Prepare an edition manifest once

Each future Bible is represented by one reviewed file:

`config/bible-intake/<resource_id>.json`

It must satisfy `schemas/bible-intake.schema.json` and contain:

- Unique resource ID, real title, exact edition and source language.
- Original provider and archive URLs from a hardcoded HTTPS host allowlist.
- **Exact SHA-256 hashes** of the original authorial source ZIP and official
  SWORD module ZIP; unknown hashes mean **do not run network acquisition
  or publish**. Retrieve and independently review source identities first.
- `source.format`: `USFX`, `USFM`, or `OSIS`; for OSIS add the
  exact XML `source.member` in the ZIP. USFX needs a reviewed explicit
  book-name crosswalk. Neither unsupported markup nor ambiguous
  source-to-compiled verse indexing is silently corrected.
- Original SWORD ID, actual `RawText` or `zText` driver,
  and two or more representative book/chapter/verse probes.
- A rights-evidence URL and rights review status. **`research_only`
  is mandatory**: even after a technical report passes, this file does
  not grant redistribution or editorial permission.

The existing `webp-research` file is an archived **research example**,
not a second Bible approved for public release. It is pinned to the
historically audited WEBP USFX and original eBible zText archives. Existing
source-only verse and note/canon differences are *expected to block full
fidelity*, not to be hidden by special cases.

## Run it

**Recommended — start from the Bible's issue (including from ChatGPT):**

Post the following exact command as a new top-level comment in an **open
`[Import]` issue**, from the repository owner's GitHub account:

```text
/bible-audit webp-research 4
```

The workflow listens for owner-authored `issue_comment` events on
`main`, verifies the issue type, and parses only a strict resource ID
and integer stage 1–7. It then runs without keeping the ChatGPT session
open and automatically posts the metadata-only summary back to that
issue. Replies by other users, malformed commands, comments on PRs, and
non-import issues are ignored. The GitHub connection used here posts
comments as the repository owner, so the assistant can initiate an
approved stage through the same issue-comment action; it need not have
a direct `workflow_dispatch` permission.

**Alternative — manual dispatch through GitHub Actions:**

Open [Actions → Audit one Bible onboarding stage (read-only)](
https://github.com/icfmp/Bible-Resources/actions/workflows/bible-staged-audit.yml),
select **Run workflow** on `main`, and provide:

- `resource_id`: the filename without `.json` (e.g. `webp-research`).
- `stage`: **1** through **7**; each execution checks just one bounded stage.
- `issue_number` (optional): the corresponding open **[Import]**
  issue; the workflow posts a short permanent *evidence* comment there.

Every run writes `stage-report.json` and `stage-summary.md` as
**metadata-only** artifacts (90-day retention), and shows the report in
the GitHub Actions run summary. If an eligible import issue is provided,
the comment holds the result beyond artifact retention, with a link to the
specific run. **It never checks the issue's box automatically**: a
complete stage gate also needs any mandatory source, rights and editorial
review documented in the issue. A failed download or a malformed source
blocks the job; a completed *diagnostic* can legitimately return
`PARTIAL`, `BLOCKED` or `REVIEW_REQUIRED` while the workflow execution
itself succeeded. A green GitHub Action is **not** a publication approval.

For local development:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_bible_stage_runner.py' -v

mkdir -p /tmp/bible-report
python scripts/bible_stage_runner.py \
  --resource-id webp-research --stage 1 --report-dir /tmp/bible-report
```

For stage 2 and above, network fetches always verify the pinned original
archives in the temporary work directory. Stages 4–5 require stock
`libsword-dev` C++ inspectors, which the GitHub workflow compiles;
stage 6 requires `diatheke`. An original OSIS stage 3/4 requires the
official, pinned schema automatically fetched by its existing approved
helper. Source and original SWORD binary never appear in the artifact.

## Automation coverage — honest limits

| Stage | Currently automated and recorded | Remains outside automated approval |
| --- | --- | --- |
| 1. Edition / rights | Config field validation and official provider URL review | **Human** textual/edition identity, duplicate baseline, legal/notes/Strong rights |
| 2. Originals | Bounded HTTPS acquisition, redirect allowlist, exact SHA-256 and safe source/SWORD ZIP preflight | Human verification of publisher source selection when first pinned |
| 3. Authorial source | USFX/USFM source inventory; original OSIS schema/XSD and verse inventory | Source-format conversion parity when needed, complete title/notes/poetry and exact edition determination |
| 4. Native vs original | Actual native `RawText`/`zText` whole-corpus comparison for **USFX** with explicit book crosswalk; OSIS native index comparison | A generic USFM conversion and full OSIS→SWORD semantic comparator; edition/canon and source-only verse conflicts |
| 5. Editorial structure | USFX numbered-note body/type/target **diagnostics** on the real native corpus | Word-position anchors, resolved source links, book introductions, poetry, Strong ordinals if present, authoritative signoff |
| 6. Reader trial | Isolated standard SWORD ZIP installation and deterministic stock `diatheke` readbacks | Another independent reader and manual visual/parallel acceptance |
| 7. Publication | Deterministic **review-required** gate, with *no* publish action | Explicit owner approval, release PR, normal repo CI, GitHub Release + Pages and live HTTP check |

An unsupported format or missing evidence is reported as **BLOCKED** or
**PARTIAL**, not silently downgraded to success. Stage 4 can report
`BLOCKED` for the original pinned WEBP anomalies even when its
stock-SWORD extraction was performed correctly.

### Resuming after a chat or Actions interruption

1. Read the resource's import issue and its last dated audit checkpoint.
2. Verify the linked run, source SHA-256 and Git commit. If the manifest
   or audit script changed, the previous result is not a certificate for
   the new bytes.
3. Re-run **only the necessary stage** with the same reviewed inputs.
   A later stage may re-download the originals to an isolated runner and
   independently re-verify their hashes; this is deliberate, not loss of
   editorial progress.
4. Keep prior completed stages in the issue, record a new comment and
   update the checkbox **only once all requirements of that stage are met**.

A ChatGPT session is **not** kept alive and is not automatically notified
at the end of an Action. The assistant can **start** an eligible run by
posting an owner-authored `/bible-audit <resource-id> <stage>` comment
in the appropriate issue, but a later message is required for the
assistant to return and interpret the completed action. The issue and
run URLs preserve the exact checkpoint for the next conversation. A
normal PR touching this automation triggers the existing pinned WEBP
research proof, without approving its original edition. No heavy
research step should be run in a long-lived chat.

## Safety and publication separation

- GitHub workflow uses `contents: read` for the audit job.
  A separate manual-run-only notification job has narrowly scoped
  `issues: write` to comment on an existing open `[Import]` issue.
- Repository/source material is never committed by this Action and no
  automated dispatch can update a SWORD ZIP, bump the module version,
  set `quality.status=approved` or deploy Bible text.
- Source download hosts are a source-controlled allowlist; archives must
  be HTTPS, bounded, complete, unchanged by redirection and SHA-256-pinned.
  ZIP files are preflighted for path traversal, duplicate member paths,
  symlinks and size limits before a separate isolated reader uses them.
- Even when original notes or Strong metadata are missing from a source,
  no generated additions, content rewriting or automatically invented
  edition relationships are permitted.
- Audit artifacts contain counts, hashes, code and reference IDs only.
  They are evidence of *which controls ran*, not independent certification
  of the publisher's identity or ownership.
