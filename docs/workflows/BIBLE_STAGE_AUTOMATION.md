# Run a Bible onboarding audit stage

**Current operator quick guide.** The full [source-first production contract](../PRODUCTION_PIPELINE.md) governs original OSIS/USFM preservation, cleanup, full validation, SWORD compilation and publication. Use the [Bible seven-stage workflow](BIBLE_7_STAGE_WORKFLOW.md) for the required checkpoints. This automation **collects read-only evidence**; it does not clean, approve, compile or publish an edition.

The original detailed WEBP research and stage-4/5 diagnostic investigations have been preserved, without deleting their evidence, in the [historical technical research appendix](../archive/BIBLE_STAGE_AUTOMATION_RESEARCH.md). That appendix documents experiments and limitations, not additional mandatory procedures.

## Prepare the reviewed intake manifest

The resource must have `config/bible-intake/<resource_id>.json` conforming to `schemas/bible-intake.schema.json`. Record the exact edition, publisher source URL(s), language, SWORD identity, driver, original archive SHA-256 and independent rights decisions.

**Stage 1** may accept explicit unknown hashes/IDs as `null` for metadata-only research without fetching content. **Stages 2–6** require independently reviewed pins and fail closed on changed upstream bytes. Do not auto-pin new publisher ZIPs.

## Optional observation before approving source hashes

In an open repository `[Import]` issue, the repository owner may post:

```text
/bible-observe frajnd-2024
```

The [original source observation workflow](../../.github/workflows/bible-observe-originals.yml) downloads into temporary runner storage and reports observed hashes/metadata without making any editorial or rights claim. Review the observed edition before approving and recording the hashes; future stages recheck them.

## Run one stage

Recommended: in an open repository `[Import]` issue, post an owner-authored top-level comment:

```text
/bible-audit webp-research 4
```

Here `webp-research` is an **example** reviewed resource ID, and `4` is the requested stage (1–7). The workflow parses the owner comment and posts a metadata-only evidence receipt to the issue.

Alternatively, use [Actions → Audit one Bible onboarding stage](https://github.com/icfmp/Bible-Resources/actions/workflows/bible-staged-audit.yml), select `main`, and specify `resource_id`, `stage` (1–7) and optionally the `issue_number`. It records `stage-report.json` and `stage-summary.md` as metadata-only artifacts (retention may be limited), alongside the run summary. Original full texts must not be put in logs or public artifacts.

For local development and the read-only runner tests:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_bible_stage_runner.py' -v
mkdir -p /tmp/bible-report
python scripts/bible_stage_runner.py \
  --resource-id webp-research --stage 1 --report-dir /tmp/bible-report
```

Stage 1 does not fetch source archives. Later stages perform pinned archive checks, and applicable native SWORD and official OSIS inspections. Do not treat a green workflow as approval: `PARTIAL`, `BLOCKED` or `REVIEW_REQUIRED` findings can still accompany a successful job.

## Resume, verify and close a checkpoint

Store the exact commit, pinned source hash, run URL, report summary, pending decisions and next stage in the corresponding GitHub issue. Revalidate the manifest and source pins before replaying a previously completed stage, and **never** tick a stage as complete solely because a diagnostic run finished.

Stage-4 diagnostics of paragraph topology, overlap, whitespace, notes, verse positions, structural milestones and original-vs-compiled native metadata require their own semantic interpretation. See the [full historical diagnostic appendix](../archive/BIBLE_STAGE_AUTOMATION_RESEARCH.md) for accumulated research and limitations; do not silently repair publisher text or change versification to satisfy an individual probe.

**Publication boundary:** these Actions do not approve rights, source transformations, native content equivalence, real reader compatibility or a public release. See [publishing](PUBLISHING.md) and the [production contract](../PRODUCTION_PIPELINE.md).
