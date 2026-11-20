# Resource workspace — directory conventions

This page defines the **directory contract**, not an inventory of particular published editions. Source availability and status must be read from the actual repository tree, provenance manifests, issues and approved release receipts.

## Resource locations

```text
sources/
  original/<type>/<language>/<module-id>/    # immutable acquired source
  cleaned/<type>/<language>/<module-id>/     # reviewed editorial master
    <source>.osis.xml                        # source-first cleaned content
    CLEANUP_MANIFEST.json                    # deterministic derivation and hashes
    editorial/
      README.md                              # edition-specific decisions
      evidence/                              # audits, source witnesses, QA
      profiles/                              # reader descriptions and approval sources
      releases/                              # versioned release receipts
      history/                               # prior editorial research
work/                                        # reproducible temporary processing
modules/<module-id>/                         # native compiled SWORD module / metadata
docs/                                        # generic project process, architecture, rules
history/                                     # superseded cross-cutting research
```

The conventional source/master basename can vary by edition; identify the exact file from `CLEANUP_MANIFEST.json`. Never assume an original OSIS exists just because a published SWORD module is present. Some original sources are publisher XML/USFM and some cleaned masters are reconstructed from approved native witnesses; mark those limits explicitly.

## Boundaries

- Keep original bytes immutable with source URL, edition, rights and SHA-256.
- Cleaned masters are reviewed derived artifacts, not automatic copies of original edition XML.
- Document source-specific exceptions **next to the resource**, not inside the generic methods.
- Never make a reader UI workaround by silently altering source text.
- `entity-index/` is a separate Bible Semantic Index workstream; do not move or normalize it as part of resource imports.
- The retired place-context dataset pipeline is not an authoritative resource workspace.

See [production](../PRODUCTION_PIPELINE.md), [workspace architecture](WORKSPACE_LAYOUT.md) and [rights](../policies/RIGHTS.md).

The dated prior resource-by-resource inventory is retained in [history](../../history/inventory/RESOURCE_WORKSPACE_INDEX_2026-11-20.md).
