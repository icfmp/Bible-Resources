# Workspace layout

**Convention:** `<resource-type>/<language>/<resource-id>/` for original, cleaned and new working sources. Resource types are `bibles`, `commentaries`, `dictionaries`, `encyclopedias` and `other`. Use a registered lowercase ISO 639 language identifier (two letters where available, otherwise the appropriate three-letter code). Do not create empty category folders or fake source editions.

```text
sources/
  original/<type>/<language>/<resource-id>/          # acquired files, unchanged
  cleaned/<type>/<language>/<resource-id>/           # reviewed editorial master
    CLEANUP_MANIFEST.json                            # derivation, hashes and changes
    editorial/
      README.md                                      # current edition decisions
      evidence/                                      # source witnesses, audits, reader QA
      profiles/                                      # edition-specific reader metadata
      releases/                                      # approved or explicitly draft receipts
      history/                                       # edition-specific historical decisions
work/<type>/<language>/<resource-id>/                # new drafts and local investigations
modules/<resource-id>/                              # native SWORD and approved metadata
catalog/v1/                                         # client-facing catalogue
sword/                                              # distributed module packages
docs/                                               # durable, generic documentation
history/                                            # old cross-resource research
reports/tooling/                                    # generated script inventory
```

## Immutable original

Preserve original source bytes and identity, archive contents, version, exact edition, URL, acquisition date, size, SHA-256 and license/rights evidence. Source files may be omitted from public Git when redistribution is not authorized; their trusted provenance still needs to be pinned. Never convert or patch originals in place or claim that a newly reconstructed OSIS file was the original author's XML.

## Reviewed cleaned edition

Create independent candidates outside the original tree. A curated master under `sources/cleaned/` requires its own pinned hashes and reversible transformation ledger. Verify all text, punctuation, verse mappings, notes, citations, headings, paragraphs, poetry, lexical markup and commentary scopes as applicable. Store resource-specific decisions and test receipts in `editorial/` — **not in global `docs/`**.

Existing historical `work/` layouts may differ. Keep existing paths required to reproduce or resume work until their references have been audited; they are not templates for new resources.

## Compiled and published output

`modules/` remains the native SWORD distribution workspace. Do not mass-relocate signed module payloads or treat file movements as a reason to republish. The `sword/` and `catalog/v1/` interface is versioned and protected by release checks.

The generated [script registry](../../reports/tooling/TOOL_REGISTRY.md) documents active tools. Reorganizing scripts requires verifying imports, workflows, tests, historical pinned callers and exact output equivalence; it is a separate task from source layout.

The independent `entity-index/` Bible Semantic Index must not be changed during this cleanup.

See the [architecture](ARCHITECTURE.md), [production contract](../PRODUCTION_PIPELINE.md), [normalization policy](../policies/NORMALIZATION_POLICY.md) and [publishing](../workflows/PUBLISHING.md).
