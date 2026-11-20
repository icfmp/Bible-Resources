# Source-first workspace layout

**Project-wide convention, adopted 2026-11-20.** This is a workspace policy,
not a change to the published SWORD installation layout or module identities.

## Canonical directory tree

```text
sources/
  original/
    bibles/<resource-id>/
    commentaries/<resource-id>/
    dictionaries/<resource-id>/
    encyclopedias/<resource-id>/
    other/<resource-id>/
  cleaned/
    bibles/<resource-id>/
    commentaries/<resource-id>/
    dictionaries/<resource-id>/
    encyclopedias/<resource-id>/
    other/<resource-id>/
work/
  bibles/<resource-id>/{drafts,audits,tests}/
  commentaries/<resource-id>/{drafts,audits,tests}/
  dictionaries/<resource-id>/{drafts,audits,tests}/
  encyclopedias/<resource-id>/{drafts,audits,tests}/
  other/<resource-id>/{drafts,audits,tests}/
modules/<resource-id>/              # published/staged SWORD + evidence; unchanged
scripts/                           # stable command-line interfaces; unchanged
tests/                             # independent regression tests; unchanged
docs/                              # cross-resource policy and historical receipts
```

The actual resource category in `modules/<resource-id>/metadata.json`
determines the typed folder; use the same stable resource ID everywhere.
Use plural directory names, **not** translated spellings, and avoid
distinguishing directories by provider or language unless two separate curated
resource IDs genuinely exist.

OSIS and USFM are the preferred source formats. Add another format only if a
resource requires it and a tested standards-based adapter already exists or is
approved. Keep the same structure for Greek/Hebrew Strong tags, morphology,
translation notes, textual variants, cross-references, footnotes, alternate
readings, poetry and comments; these are **source content/annotations**, not
compiler decorations.

### Original sources

Under `sources/original/<type>/<resource-id>/`, retain the **exact** acquired
source bytes when their repository redistribution rights permit it. Never
silently edit originals, reserialize XML, normalize Unicode, strip annotations,
or replace one edition with another. Pin origin URL, revision, exact edition,
size, SHA-256, rights/annotations/licensing and any original companion archive.

If mirroring is not permitted, **do not commit the bytes**: keep them in
controlled storage and retain only permissible metadata/checksums/URLs in the
resource manifest. Do not create misleading empty source files.

### Cleaned sources

Under `sources/cleaned/<type>/<resource-id>/`, retain our **reviewed,
reproducible editorial master** as OSIS/USFM or a deliberately approved
standard. Each source has a reversible source-bound change ledger and
source/cleaned hashes. Standardize *presentation and machine structure*,
never authorial content silently. Check whole-corpus preservation of words,
punctuation, verses, notes, headings, poetry, Strong/morphology, word-level
alignment and references where present. Track independent edition witnesses
and rights separately.

Only commit a cleaned source if redistribution and modification rights allow
it; otherwise keep a protected master and document limitations of public
reproducibility.

### Working files

Under `work/<type>/<resource-id>/`, store **unfinished, nonauthoritative**
drafts, bounded test inputs, unpublished reports, screenshots/reader QA and
transient build experiments. Prefer disposable local output ignored by Git
for generated intermediates. Do not duplicate a cleaned canonical source here
or publish unrestricted raw source text via public Actions artifacts.
Committed evidence must have a durable provenance role.

Canonical draft subdirectories are `drafts/`, `audits/` and `tests/`; create
a directory only when real content exists. Do not create dozens of empty
`production/`, `final-final/` or date-specific folders.

### Distribution and tooling

`modules/<resource-id>/` retains its **existing stable layout** for verified
SWORD files and immutable source/release attestations. Do not rearrange
`payload/mods.d/` or `payload/modules/`: SWORD readers rely on those paths.
Official release-before-Pages publication remains authoritative.

Keep stable script entrypoints in `scripts/` until all historical callers,
GitHub Actions, tests, import statements, user-facing commands and release
tags have been audited. Distinguish:
- generic reusable acquisition/validation/normalization/build/reader tooling;
- resource-specific reviewed recipes and manifests;
- historical probes or trial scripts necessary to reproduce a past decision.

A historical script is **not** safe to delete merely because an inventory
suggests `HISTORICAL/ARCHIVE`. Archive only after auditing historical tags and
making all current checks pass; avoid replacing a working tool with a stack of
compatibility wrappers. See [tool registry](TOOL_REGISTRY.md).

## Existing historical layout: compatibility phase

The following paths predate this policy and must **not** be renamed or removed
without a separate, fully tested path-migration PR:

- `sources/cleaned/mhc/`: documentation and provenance of the original MHC
  experiment, **not a committed cleaned OSIS body**.
- `work/mhcc-modern/`: ~1,300 historically versioned modern-commentary
  manuscripts and review receipts. **Do not call this scratch to be deleted**:
  retain existing references, source-diff hashes and final-release proof.
- `work/commentaries/mhc-crosswire/experiments/ccel-imp/`: archived historical CCEL
  feasibility adapter and its tests, **not a supported importer**. This was
  moved with byte-identical Python source and updated historical workflow.

These are **legacy-compatible paths**, not new locations to target. New
projects and future versioned source editions follow the typed structure
immediately. Historical source migrations must preserve Git history, evidence
identity, and paths referenced by workflows, scripts, tests and prior PRs.
Do not silently modify sealed receipts or source-bound content hashes to
make a move appear clean.

## Migration gates for each existing resource

1. Inventory old paths, exact tracked blob hashes and current + historical
   callers; establish the versioned release and permissions baseline.
2. Move **one resource at a time** only if old-path references can be migrated
   without invalidating an immutable proof; otherwise retain legacy paths.
3. Update tests, workflows, relative imports, links, source manifests, report
   generators and tool registry together. Archive historical evidence rather
   than patching its meaning.
4. Confirm `git diff --summary` identifies expected moves, every tracked
   source blob is accounted for, no original/cleaned text is lost, and no
   unexpected large-source data is introduced.
5. Run complete unit tests, repository validation, registry consistency,
   deterministic package generation, actual SWORD smoke, and relevant
   cross-reader tests on affected **compiled modules**.
6. Never republish an immutable release solely because a workspace path
   changed. New publication requires the existing explicit approval process.

## Script cleanup: deliberately safe, not cosmetic

The generated registry records 177 top-level scripts (26 KEEP_GENERIC,
3 GENERALIZE, 10 MERGE, 9 HISTORICAL/ARCHIVE, 129 UNDECIDED) at the
2026-11-20 inventory baseline. These are **review classifications**, not
177 currently maintained command-line contracts or a license to remove 151.

The next actual lifecycle consolidation needs independent caller and behavior
checks; prioritise merge candidates with overlapping tests, archive only after
a proven replacement, and preserve reproducible release evidence. Never add
a new script purely to support folder naming. This preparatory migration
intentionally changes **no executable script** and leaves the MHC, MHCC,
HMCC Modern, Darby and Segond SWORD payload bytes untouched.

See [six-phase editorial workflow](SOURCE_FIRST_EDITORIAL_PIPELINE.md),
[editorial rules](EDITORIAL_RULES.md), [rights policy](RIGHTS.md) and
[publication gates](PUBLISHING.md).
