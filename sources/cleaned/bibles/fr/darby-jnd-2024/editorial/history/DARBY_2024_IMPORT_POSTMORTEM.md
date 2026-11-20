# Darby 2024 — lessons retained from original import

**Retrospective only.** The [0.1.1 release](../releases/DARBY-JND-2024-0.1.1.md), [manifest](../../CLEANUP_MANIFEST.json) and [reader QA](../evidence/darby-2024-0.1.1-final-reader-qa.md) control current editorial facts. The original dated stage-by-stage timings are in Git history and the [import issue #62](https://github.com/icfmp/Bible-Resources/issues/62), not an ongoing production procedure.

## Lessons with continuing value

1. **Separate original evidence from interpretation.** Verify official BPC source identity, source SHA, legal basis and exact versification before compiling. A successful import alone does not prove edited source fidelity.
2. **Run a full structure/cross-reference inventory early.** Detect verse IDs, notes, introductions, poetry, true typographic/division marks and unusual XML before expensive native reader builds. Never silently map a source verse to a different canonical system.
3. **Distinguish editorial stars from text-critical stars.** Darby's reviewed 521 structural markers could be encoded as non-displayed metadata, but one genuine source text-critical star had to remain visible. This is **edition-specific evidence**, not a universal regex.
4. **Prevent XML pretty-print whitespace from leaking into SWORD.** The 4,690 reviewed indentation artifacts were source-formatting bytes, not authorial spaces; use exact original/source/native semantic comparison before removing them.
5. **Limit redundant builds.** Batch source-wide read-only inventories and reuse their source-hash-bound receipts. Stop early on proven data loss; retain a separate real reader gate before release.
6. **Keep source correction and app display bugs separate.** A SWORD reader's handling of legitimate paragraph, note or milestone markup cannot justify silently rewriting biblical prose.

See [source production workflow](../../../../../../../docs/PRODUCTION_PIPELINE.md) and [paragraph technical QA](../../../../../../../docs/technical/OSIS_PARAGRAPH_RENDERING_QA.md) for current reusable methods.

No historical milestone or prior success supplies automatic approval for a future Darby revision or another translation.
