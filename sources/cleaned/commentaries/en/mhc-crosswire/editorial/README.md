# Editorial record — Matthew Henry's Commentary (complete, English)

**Scope:** source-attested corrected MHC OSIS used for the existing 0.1.0 release; not a generic rule for commentary remapping.

## Decisions and boundaries

- Preserve Matthew Henry's prose and division structure; do not silently rewrite or truncate it.
- The approved reconstruction ledger distinguishes **11 empty inert emphasis tags**, **3 invalid range endpoints**, **25 cross-reference destinations**, **6 overlap reindex groups** and **one chapter-introduction reclassification**. Those are edition-specific repairs, not universal assumptions about source content.
- Keep chapter introductions, passage/verse scopes and overlapping entries semantically distinguishable. Do not duplicate one chapter-level authorial comment across verse entries merely to accommodate a reader.
- Each stage from original through cosmetic/endpoints/cross-references/chapter intro is pinned by its own SHA-256 in [CLEANUP_MANIFEST.json](../CLEANUP_MANIFEST.json). Do not extrapolate these repairs to unrelated editions.

## Evidence

- [Original and cleaned stages](../CLEANUP_MANIFEST.json)
- [MHC 0.1.0 release receipt](../../../../../../docs/releases/MHC-0.1.0.md)
- [Source attestation workflow](https://github.com/icfmp/Bible-Resources/actions/runs/44554276085)

**Status:** documented historical decisions. Future changes require a new source-backed ledger and review.
