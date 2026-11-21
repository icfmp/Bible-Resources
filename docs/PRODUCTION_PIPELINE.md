# Source-first production: executable editorial contract

**Status:** canonical operational entry point for new or revised resources. This document specifies required evidence, not a claim that all stages are automated. This is the **single authoritative production process**. The [Bible](workflows/BIBLE_7_STAGE_WORKFLOW.md) and [commentary](workflows/COMMENTARY_7_STAGE_WORKFLOW.md) seven-stage checklists track progress but do not define competing acceptance standards. Where policies disagree, stop and resolve the discrepancy in a reviewed PR; do not silently select the weaker rule.

The proposed [BRNP profile](architecture/BRNP.md) is deferred to issue #451 and is **not** a release gate. The existing official XSD, source-fidelity and SWORD/reader acceptance checks remain authoritative.

**Numbering:** Sections 0–6 below explain the *technical dependency order*, starting with the prerequisite source/rights gate (0). The separate seven-stage [Bible checklist](workflows/BIBLE_7_STAGE_WORKFLOW.md) and [commentary checklist](workflows/COMMENTARY_7_STAGE_WORKFLOW.md) are **progress-reporting views**. In particular the Bible checklist calls native index/text auditing stage 4 and full source-to-native semantic/structural parity stage 5. This does not postpone source-to-cleaned fidelity until after compilation: that comparison is required **before** any candidate is approved for the build, and must be verified again against the native output afterwards. No item is waived because two guides group tasks differently.

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
   OR preserve an unchanged, independently audited stock binary
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

**Required evidence:** inventory counts, anomaly list (with source location or SWORD entry key), full original checksums, and explicit classification of unclear structures. See [source inventory](technical/SOURCE_INVENTORY.md), [source OSIS inventory](technical/SOURCE_OSIS_INVENTORY.md) and [versification policy](policies/VERSIFICATION_POLICY.md).

## 2. Normalize structure; do not rewrite the author's meaning

For every cleaned resource, write its **edition-specific editorial decisions** to `sources/cleaned/<type>/<language>/<resource-id>/editorial/README.md` (and link to more detailed evidence under that directory as necessary). Global policies remain in `docs/`; `CLEANUP_MANIFEST.json` stays the machine-readable recovery/hash record. Do not confuse approved historical decisions with authorization to change new text. See [module-local editorial records](../sources/cleaned/README.md).


**For a source-derived or corrected rebuild**, produce a **new** deterministic candidate under `work/<type>/<language>/<resource-id>/`, then, after review, the curated master under `sources/cleaned/<type>/<language>/<resource-id>/`. Use the appropriate supported source format (OSIS, USFM/USFX or another reviewed standard adapter) with exact provenance. **For genuinely unchanged upstream compiled SWORD stock**, do not invent authoring XML or require a fictional cleaned source master. Instead pin the exact upstream binary and original metadata, and retain its independent native source/rights evidence. These are two separate verification routes, not exemptions from fidelity. Prefer standard elements over presentation-only HTML while keeping meaningful distinctions.

Allowed candidates include documented repair of invalid markup, removal of objectively redundant display artifacts, and restoration of source-attested paragraphs, poetry or headings. **Not automatically allowed:** wording changes, punctuation changes, translations, textual variants, versification changes, added/deleted notes, inferred cross-reference targets, changes in emphasis that carry meaning, or reshaping commentary ranges for a particular reader.

Record every transformation rule, why it is necessary, how it can be reversed, and affected entry IDs; exceptions belong in reviewed source/edition metadata, not hidden one-off code. Distinguish source error, editorial peculiarity, compiler behavior and reader rendering defects. If formatting is ambiguous, preserve it or flag it for review rather than pretending to fix it.

**Required evidence:** deterministic script/commit and exact input/output hashes; machine-readable change inventory; human-readable semantic and structural diff; explicit list of unresolved decisions. See [normalization contract](policies/NORMALIZATION_POLICY.md), [editorial rules](policies/EDITORIAL_RULES.md), [semantic fidelity](policies/OSIS_SEMANTIC_FIDELITY.md).

## 3. Validate the cleaned master and prove fidelity

For a rebuilt source, run the official pinned OSIS schema **where applicable** (or the source's own format validator), plus resource-specific guards. Compare the **entire** original and cleaned corpora at stable reference/entry keys; never rely on text-only aggregate hashes or on representative samples alone. For **unchanged compiled stock**, verify its original published binary/configuration bytes and native content/index identity instead of claiming a nonexistent source-to-cleaned XML comparison. Any claim of independently preserved authorial-source fidelity still needs its own original-authoring witness and proof. Count preserved, changed, inserted, deleted and remapped entries, and check structure separately from words and punctuation. Verify notes, references, labels, destinations, headings, poetry, paragraphs, introductions, metadata and word-level alignments.

Changes must match an approved, reversible ledger; unexplained changes fail closed. Recheck against an **independent, accurately identified edition witness** when correcting an apparent source defect. Do not conflate a modern translation or a later edition with the original edition. Commentary coverage may be by chapter, verse or passage range; respect the author's actual divisions and make any reader fallback explicit at the application layer.

For Bible resources, validate the exact native versification including absent/omitted verses and nonstandard systems. For commentaries, validate annotateRef / section scope and internal/external link behavior. For Strong/lemma data, verify tokens, occurrence order and original-language directionality; do not infer lexical links purely from spelling.

**Required evidence:** exhaustive before/after counts and exceptions, schema report, source-versus-witness decisions, and signed editorial review. See [main text fidelity](policies/MAIN_TEXT_FIDELITY.md), [source-native main text](technical/SOURCE_NATIVE_MAIN_TEXT.md), [source-native notes](technical/SOURCE_NATIVE_NOTES_AUDIT.md), [source-native index](technical/SOURCE_NATIVE_INDEX_AUDIT.md), [commentary policy](policies/COMMENTARY_POLICY.md).

## 4. Compile and independently inspect SWORD

**For a reviewed source-derived rebuild**, compile with existing upstream SWORD conventions/tools and the repository's approved build path. **For unchanged stock**, preserve the original upstream SWORD payload/configuration byte identity and package only through the approved stock route; do not silently recompile it or call it a rebuilt module. In both cases preserve metadata, module identity, rights notices and encoding. Pin compiler version, options, input hash and output native file inventory. Confirm output is reproducible where the existing contract specifies reproducibility; distinguish different ZIP packaging bytes from changed underlying SWORD entries.

Perform **full native readback** (keys, text, markup, metadata, commentary scope, verse mapping, notes and links as applicable) and compare the results to the approved cleaned master **for a rebuild**, or to the exact pinned upstream original SWORD payload and separately proven authorial witnesses **for stock reuse**. Use the native audits and stock SWORD probes already present in the repository. Do not claim a complete round-trip gate unless it has actually been run and passed for this source type.

**Required evidence:** compiler/tool versions, reproducible build manifest, native full-corpus parity/exception report, archive SHA-256 and package inventory. See [native raw witness](technical/NATIVE_SWORD_RAW_WITNESS.md), [whole corpus](technical/NATIVE_SWORD_WHOLE_CORPUS.md), [stable reference audit](technical/STABLE_SWORD_REFERENCE_AUDIT.md).

## 5. Test in independent readers

Install the exact candidate in an external SWORD reader such as Xiphos; use another reader where coverage warrants it (e.g. AndBible/JSword). Verify representative **high-risk** cases in the GUI: introductory sections, chapter-only commentary, verse/range anchors, omitted verses, paragraphs and poetry, notes, hyperlinks and their true destinations, cross-book navigation, language direction and nonstandard versification. Distinguish a reader display bug from a source or SWORD payload defect. Record tested application/version, environment, exact candidate hashes, screenshots and failure classification.

Reader samples supplement, **never replace**, exhaustive native parity. Do not modify the separate `icfmp/Bible` application to conceal source defects. See [reader QA](technical/OSIS_PARAGRAPH_RENDERING_QA.md).

## 6. Release approval, publication, and retention

Before publication, record evidence of rights and editorial approval, source lineage, completed/blocked checks, unresolved exceptions, exact module version and proposed release URLs. A reviewer must be able to reproduce outputs from the pinned original and scripts; keep prior versions and proof receipts. Publish only through the repository's existing verified **versioned GitHub Release before Pages catalogue** protocol. Download the public artifacts and independently compare sizes/hashes against the approved release receipts. Do not silently overwrite published bytes or claim publication from a merely staged private artifact.

**Required evidence:** signed-off version manifest, successful required checks, immutable release receipts, live-download parity, updated catalogue and release documentation. See [publishing](workflows/PUBLISHING.md), [catalogue update protocol](workflows/CATALOGUE_UPDATE_PROTOCOL.md), and each resource's own `sources/cleaned/<type>/<language>/<id>/editorial/releases/` directory for edition-specific receipts.

## Mandatory evidence record for every resource

| Field | Minimum record |
| --- | --- |
| Identity/rights | Edition, provenance, license and component-specific permissions |
| Originals | Source URLs, immutable bytes, file hashes |
| Transformation / stock route | For rebuilds: rule IDs, code revision, input/output hashes and reversible ledger; for unchanged stock: proof of original native payload/configuration byte identity and explicit `no conversion` declaration |
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
