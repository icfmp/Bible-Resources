# Source-first production: executable editorial contract

**Status:** canonical operational entry point for new or revised resources. This document specifies required evidence, not a claim that all stages are automated. It complements the established [six-phase policy](SOURCE_FIRST_EDITORIAL_PIPELINE.md) and the [seven-stage Bible](BIBLE_7_STAGE_WORKFLOW.md) and [commentary](COMMENTARY_7_STAGE_WORKFLOW.md) checkpoint workflows. Where policies disagree, stop and resolve the discrepancy in a reviewed PR; do not silently select the weaker rule.

## The production chain

```text
identify source, edition, rights
        ↓
pin immutable ORIGINAL (OSIS / USFM / justified standard adapter)
        ↓
inventory every source structure and versification
        ↓
produce CLEANED candidate (deterministic, reviewed transformations)
        ↓
validate XML/standard + audit COMPLETE original ↔ cleaned differences
        ↓
independently verify editorial content against exact source witnesses
        ↓
audit annotations / notes / references / section mapping / word alignment
        ↓
compile SWORD from the APPROVED cleaned master
        ↓
native full-corpus readback + independent readers + reproducibility checks
        ↓
owner/editorial/rights sign-off → versioned Release → Pages catalogue
```

**Blocking rule:** no stage advances based solely on successful compilation, visual plausibility, a sample chapter, or a green CI check that does not exercise the required evidence. A previous release is not authorization for a new editorial revision.

## 0. Edition identity and legal gate (before any processing)

Record the exact title, author/translator, edition/date, language, source owner, authoritative URL, acquisition date, format, license evidence, rights for text *and* annotations/links/editorial additions, and SWORD version/versification/driver where relevant. Resolve conflicts among witnesses or document them as open. A generic statement such as "public domain" must be traceable to a particular edition and component. Never present a derived cleaned edition as the publisher's original.

**Required evidence:** rights/edition decision, original download URL, SHA-256 and file size, and a `PROVENANCE.json` or the repository's existing approved equivalent. No redistribution if permissions remain unresolved.

## 1. Preserve and inventory the original

Store unmodified originals at `sources/original/<type>/<language>/<resource-id>/`; never rewrite them in place. The canonical categories are `bibles`, `commentaries`, `dictionaries`, `encyclopedias` and `other`. Preserve archive bytes (and bundled ancillary materials), source filenames and hashes.

Perform a **read-only** full inventory: book/chapter/verse or commentary-entry keys, source-native versification, omitted verses, introductions, paragraph boundaries, poetry, titles, tables, quotations, punctuation, notes, cross-references, link destinations, milestones, word/lemma/Strong/morphology markup, original-language directionality, invalid XML and unusual constructs. Capture totals and unexpected constructs; do not fabricate missing verses or move commentary to arbitrary verse keys.

**Required evidence:** inventory counts, anomaly list (with source location or SWORD entry key), full original checksums, and explicit classification of unclear structures. See [source inventory](SOURCE_INVENTORY.md), [source OSIS inventory](SOURCE_OSIS_INVENTORY.md) and [versification policy](VERSIFICATION_POLICY.md).

## 2. Normalize structure; do not rewrite the author's meaning

For every cleaned resource, write its **edition-specific editorial decisions** to `sources/cleaned/<type>/<language>/<resource-id>/editorial/README.md` (and link to more detailed evidence under that directory as necessary). Global policies remain in `docs/`; `CLEANUP_MANIFEST.json` stays the machine-readable recovery/hash record. Do not confuse approved historical decisions with authorization to change new text. See [module-local editorial records](../sources/cleaned/README.md).


Produce a **new** deterministic candidate under `work/<type>/<language>/<resource-id>/`, then, after review, the curated master under `sources/cleaned/<type>/<language>/<resource-id>/`. Use genuine OSIS or USFM; any adapter must be separately reviewed and preserve source provenance. Prefer standard elements over presentation-only HTML while keeping meaningful distinctions.

Allowed candidates include documented repair of invalid markup, removal of objectively redundant display artifacts, and restoration of source-attested paragraphs, poetry or headings. **Not automatically allowed:** wording changes, punctuation changes, translations, textual variants, versification changes, added/deleted notes, inferred cross-reference targets, changes in emphasis that carry meaning, or reshaping commentary ranges for a particular reader.

Record every transformation rule, why it is necessary, how it can be reversed, and affected entry IDs; exceptions belong in reviewed source/edition metadata, not hidden one-off code. Distinguish source error, editorial peculiarity, compiler behavior and reader rendering defects. If formatting is ambiguous, preserve it or flag it for review rather than pretending to fix it.

**Required evidence:** deterministic script/commit and exact input/output hashes; machine-readable change inventory; human-readable semantic and structural diff; explicit list of unresolved decisions. See [normalization contract](NORMALIZATION_POLICY.md), [editorial rules](EDITORIAL_RULES.md), [semantic fidelity](OSIS_SEMANTIC_FIDELITY.md).

## 3. Validate the cleaned master and prove fidelity

Run the official pinned OSIS schema where applicable, plus the resource-specific guards. Compare the **entire** original and cleaned corpora at stable reference/entry keys; never rely on text-only aggregate hashes or on representative samples alone. Count preserved, changed, inserted, deleted and remapped entries, and check structure separately from words and punctuation. Verify notes, references, labels, destinations, headings, poetry, paragraphs, introductions, metadata and word-level alignments.

Changes must match an approved, reversible ledger; unexplained changes fail closed. Recheck against an **independent, accurately identified edition witness** when correcting an apparent source defect. Do not conflate a modern translation or a later edition with the original edition. Commentary coverage may be by chapter, verse or passage range; respect the author's actual divisions and make any reader fallback explicit at the application layer.

For Bible resources, validate the exact native versification including absent/omitted verses and nonstandard systems. For commentaries, validate annotateRef / section scope and internal/external link behavior. For Strong/lemma data, verify tokens, occurrence order and original-language directionality; do not infer lexical links purely from spelling.

**Required evidence:** exhaustive before/after counts and exceptions, schema report, source-versus-witness decisions, and signed editorial review. See [main text fidelity](MAIN_TEXT_FIDELITY.md), [source-native main text](SOURCE_NATIVE_MAIN_TEXT.md), [source-native notes](SOURCE_NATIVE_NOTES_AUDIT.md), [source-native index](SOURCE_NATIVE_INDEX_AUDIT.md), [commentary policy](COMMENTARY_POLICY.md).

## 4. Compile and independently inspect SWORD

Build with existing upstream SWORD conventions/tools and the repository's approved build path; preserve metadata, module identity, rights notices, and encoding. Pin compiler version, options, input hash and output native file inventory. Confirm output is reproducible where the existing contract specifies reproducibility; distinguish different ZIP packaging bytes from changed underlying SWORD entries.

Perform **full native readback** (keys, text, markup, metadata, commentary scope, verse mapping, notes and links as applicable) and compare it to the approved cleaned master. Use the native audits and stock SWORD probes already present in the repository. Do not claim a complete round-trip gate unless it has actually been run and passed for this source type.

**Required evidence:** compiler/tool versions, reproducible build manifest, native full-corpus parity/exception report, archive SHA-256 and package inventory. See [native raw witness](NATIVE_SWORD_RAW_WITNESS.md), [whole corpus](NATIVE_SWORD_WHOLE_CORPUS.md), [stable reference audit](STABLE_SWORD_REFERENCE_AUDIT.md).

## 5. Test in independent readers

Install the exact candidate in an external SWORD reader such as Xiphos; use another reader where coverage warrants it (e.g. AndBible/JSword). Verify representative **high-risk** cases in the GUI: introductory sections, chapter-only commentary, verse/range anchors, omitted verses, paragraphs and poetry, notes, hyperlinks and their true destinations, cross-book navigation, language direction and nonstandard versification. Distinguish a reader display bug from a source or SWORD payload defect. Record tested application/version, environment, exact candidate hashes, screenshots and failure classification.

Reader samples supplement, **never replace**, exhaustive native parity. Do not modify the separate `icfmp/Bible` application to conceal source defects. See [reader QA](OSIS_PARAGRAPH_RENDERING_QA.md) and [onboarding playbook](RESOURCE_ONBOARDING_PLAYBOOK.md).

## 6. Release approval, publication, and retention

Before publication, record evidence of rights and editorial approval, source lineage, completed/blocked checks, unresolved exceptions, exact module version and proposed release URLs. A reviewer must be able to reproduce outputs from the pinned original and scripts; keep prior versions and proof receipts. Publish only through the repository's existing verified **versioned GitHub Release before Pages catalogue** protocol. Download the public artifacts and independently compare sizes/hashes against the approved release receipts. Do not silently overwrite published bytes or claim publication from a merely staged private artifact.

**Required evidence:** signed-off version manifest, successful required checks, immutable release receipts, live-download parity, updated catalogue and release documentation. See [publishing](PUBLISHING.md), [catalogue update protocol](CATALOGUE_UPDATE_PROTOCOL.md), and [releases](releases/).

## Mandatory evidence record for every resource

| Field | Minimum record |
| --- | --- |
| Identity/rights | Edition, provenance, license and component-specific permissions |
| Originals | Source URLs, immutable bytes, file hashes |
| Transformation | Rule IDs, code revision, input/output hashes, reversible change ledger |
| Content fidelity | Full-corpus entries, semantic/punctuation diffs, approved exceptions |
| Structure | Paragraphs, headings, poetry, intros, notes, links, versification, alignment |
| SWORD | Compiler/driver/version, native inventory, parity and archive checksums |
| Readers | Exact module hash, tested readers/builds, high-risk screenshots/observations |
| Approval | Editorial decision, blocking issues, publication authorization |
| Publication | Release receipts, Pages catalogue, independently checked downloads |

## Failure handling and resumption

- **Unknown source format or missing original:** stop; don't synthesize a source from a rendered screen.
- **Schema failure:** isolate the exact original/candidate location; do not suppress warnings indiscriminately.
- **Unexpected wording, punctuation or note delta:** block; correct the transformation or obtain explicit editorial review.
- **Unclear reference target or textual variant:** keep as unresolved rather than inventing a destination or verse.
- **Native SWORD mismatch:** classify compiler/configuration/index effect; do not bless a reader screenshot as proof.
- **Reader-only defect:** report against the reader/application with reproduced content, leaving the authored source intact.
- **Unapproved rights or new editorial edition:** no distribution.
- **Interrupted work:** resume from the last evidence-backed GitHub issue/PR checkpoint, checking original hashes and current `main`; never assume a past CI result certifies new inputs.

## Current implementation reality

The project has stage runners, read-only source audits, schema guards, native tests and release protections, but **the universal OSIS/USFM normalization and full source→SWORD round-trip pipeline is not yet demonstrated for every resource category**. Do not label these aspirational requirements as tests already passed. Track implementation gaps in [#3](https://github.com/icfmp/Bible-Resources/issues/3), [#28](https://github.com/icfmp/Bible-Resources/issues/28) and [#83](https://github.com/icfmp/Bible-Resources/issues/83); tool consolidation in [#430](https://github.com/icfmp/Bible-Resources/issues/430).

**Boundary:** `entity-index/` (Bible Semantic Index) is an independent workstream. No source-pipeline cleanup or documentation reorganization is permission to modify it.
