# Workspace layout

**Convention:** `<resource-type>/<language>/<resource-id>/` for original, cleaned and new working sources. Resource types are `bibles`, `commentaries`, `dictionaries`, `encyclopedias` and `other`. Use a registered lowercase ISO 639 language identifier (two letters where available, otherwise the appropriate three-letter code). Do not create empty category folders or fake source editions.

```text
sources/
  original/<type>/<language>/<resource-id>/          # acquired files, unchanged
  cleaned/<type>/<language>/<resource-id>/           # reviewed master when rebuilt; edition evidence and decisions
    CLEANUP_MANIFEST.json                            # derivation, hashes and changes
    editorial/
      README.md                                      # current edition decisions
      evidence/                                      # source witnesses, audits, reader QA
      profiles/                                      # edition-specific reader metadata
      releases/                                      # approved or explicitly draft receipts
      history/                                       # edition-specific historical decisions
modules/<resource-id>/                              # native SWORD and approved metadata
  tools/                                             # only still-needed edition-specific QA/replay scripts
scripts/                                            # reusable production and audit commands
  research/bible/                                    # reusable OSIS/native evidence libraries
catalog/v1/                                         # client-facing catalogue
sword/                                              # distributed module packages
docs/                                               # durable, generic documentation
reports/tooling/                                    # generated script inventory
```

## Immutable original

Preserve original source bytes and identity, archive contents, version, exact edition, URL, acquisition date, size, SHA-256 and license/rights evidence. Source files may be omitted from public Git when redistribution is not authorized; their trusted provenance still needs to be pinned. Never convert or patch originals in place or claim that a newly reconstructed OSIS file was the original author's XML.

## Reviewed cleaned edition

Create independent candidates outside the original tree. **A source-derived curated master** under `sources/cleaned/` requires its own pinned hashes and reversible transformation ledger. An edition distributed as **byte-identical upstream stock SWORD** may have edition-specific rights/reader evidence and an editorial index without a reconstructed OSIS master; do not create fictitious source files just to fill the example tree. Verify all text, punctuation, verse mappings, notes, citations, headings, paragraphs, poetry, lexical markup and commentary scopes as applicable. Store resource-specific decisions and test receipts in `editorial/` — **not in global `docs/`**.

Prepare source candidates in a Git branch and disposable local directories, not in a permanent tracked `work/` tree. Commit a reviewed candidate to the edition-owned `sources/cleaned/` only with a reversible transformation ledger in its `editorial/` folder. Historical research remains available in immutable Git revisions. The released HMCC Modern SWORD `TextSource` historically references the old manuscript tree; that exact historic content is recoverable at commit `c96bebf42d8e0eba62fa961f7f16a00806a50e2c` without altering signed module bytes.

Shared read-only Bible/OSIS evidence with no independent CLI belongs under [`scripts/research/bible/`](../../scripts/research/bible/README.md). Historical cross-resource research is available through immutable Git revisions, not maintained as an alternate production path. The [document relocation provenance ledger](../technical/DOCUMENT_RELOCATIONS.json) preserves original file identities. These tools never substitute for editorial or publication approval. Keep the actual stable producer/validator commands in `scripts/` and edition-owned scripts under `modules/<resource-id>/tools/`, after verifying real workflow and test consumers.

## Compiled and published output

`modules/` remains the native SWORD distribution workspace. Do not mass-relocate signed module payloads or treat file movements as a reason to republish. The `sword/` and `catalog/v1/` interface is versioned and protected by release checks.

The generated [script registry](../../reports/tooling/TOOL_REGISTRY.md) documents active tools. Reorganizing scripts requires verifying imports, workflows, tests, historical pinned callers and exact output equivalence; it is a separate task from source layout.

## Edition-specific documentation retention

Each `editorial/README.md` should fit on one readable page: **what was decided, why, what is still uncertain, and the authoritative proof to consult**. Keep the actual signed profiles, original rights/approval witnesses, immutable source/release hashes, reproducible transformation plans and native-reader validation receipts. Do **not** keep repeated draft release notes, unsubmitted correspondence, private candidate status logs or iterative machine snapshots once final evidence supersedes them. Historical research is recoverable from Git when needed; remove files from the active tree only after checking they are not referenced by current plans, workflows or approved artifact hashes. Never rewrite a signed/hashed profile merely to tidy wording or links.

The independent [Bible Semantic Index repository](https://github.com/icfmp/Bible-Resources-Semantic-Index) owns BSI development. This repository retains only historical BSI releases and their associated provenance.

See the [architecture](ARCHITECTURE.md), [production contract](../PRODUCTION_PIPELINE.md), [normalization policy](../policies/NORMALIZATION_POLICY.md) and [publishing](../workflows/PUBLISHING.md).
