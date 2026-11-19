# Source-first editorial production: OSIS/USFM → SWORD

**Status:** project-wide editorial production policy, adopted 2026-11-19.
**Scope:** Bibles, commentaries and other compatible resources, subject to their
specific formats and legal rights.

> **Preserve the work. Standardize the representation. Keep the editor invisible.**

Bible Resources publishes **clean, standards-based, source-faithful digital
editions**. We do not perpetuate a digital publisher's arbitrary typography,
formatting artifacts or nonstandard markup merely because they appear in its
OSIS, USFM or SWORD package. The curated structured source, not an opaque SWORD
binary, is the preferred **maintainable editorial master**; SWORD is a
reproducible distribution product.

This document describes the **six practical production phases**. It does
**not** replace the existing [seven-stage Bible onboarding](BIBLE_7_STAGE_WORKFLOW.md)
or [seven-stage commentary onboarding](COMMENTARY_7_STAGE_WORKFLOW.md):
their incremental evidence checkpoints and approval gates remain mandatory.
The same phases apply to both, with the resource-specific validation rules
of those workflows.

## Accepted input formats: minimal by design

1. **OSIS** — preferred when the real, identifiable publisher/authoring source
   exists, particularly for Bible texts and commentaries.
2. **USFM** — equally valid when the authoritative input is a USFM edition,
   especially for Bibles. **Do not convert USFM to OSIS merely for conformity.**
3. **Other standards** — only when essential for the resource (e.g. TEI for
   dictionaries) or when neither OSIS nor USFM is available; approve a
   **standards-based adapter** and its test burden before adding support.

No per-translation or per-commentary importer, proprietary intermediate
format, redundant conversion script, or undocumented special-case patch.
Prefer existing CrossWire/SWORD and reviewed standard libraries; reuse the
same validators, reference resolution and compiler path across resources.
If the actual input is **only compiled SWORD**, treat that as a separately
proven fallback and do **not** pretend it is an original OSIS/USFM file.
An OSIS `SourceType` tag inside a SWORD `.conf` does not supply the
original OSIS authoring source.

## Phase 1 — Acquire and identify the source

**Goal:** obtain the best faithful, editable source of the **exact** work and
edition, not simply the easiest downloadable version.

- Identify author/translator, exact title and edition, revision, date,
  language, canon, versification, source publisher, acquisition URL and format.
- Record a cryptographic SHA-256 and size of each exact original file or archive.
  Preserve original bytes unchanged for provenance and rollback.
- Verify **redistribution AND modification rights** for text and separately
  authored notes, headings and other additions. A public-domain author or
  a downloadable source does not automatically license modern digital edits.
  Unclear rights block public release; unlicensed input remains out of the
  public repository and workflow artifacts.
- Inventory source content/structures and, if an upstream compiled SWORD
  edition exists, record its exact identity separately as a useful witness.
- Start or continue a resource-specific tracking issue with immutable source
  references and verified/pending states.

**Gate:** the original is pinned, the intended edition is identifiable,
format support is known, and redistribution/derivative-rights questions
are explicitly classified.

## Phase 2 — Normalize and clean the structure

**Goal:** produce one standards-compliant, semantically clean **curated source**.

- Validate against the official, version-pinned standard (OSIS schema, USFM
  syntax and available standard validators) **before and after** processing.
- Standardize structural tags and their hierarchy: Bible books/chapters/verses,
  paragraphs, titles, introductions, poetry and line levels, quotations,
  commentary sections/ranges, tables, notes and cross-reference markup.
- Remove redundant formatting wrappers, nonsemantic decorations, stray
  asterisks/backslashes/markup residues, incorrect escapes and unneeded spaces;
  normalize whitespace and Unicode only when the operation cannot change
  meaningful content, with source-aware tests.
- Represent semantics in **standard markup**, not embedded fonts, colors or
  editor-specific layout instructions. Styling belongs to the reader. One
  equivalent semantic structure should have one consistent representation
  across resources.
- Eliminate arbitrary historical **presentation conventions** where they do
  not encode the author/edition's meaning. Do not retain nonstandard markup
  merely out of loyalty to a digital distributor.

**Mandatory distinction:** typography and encoding are not automatically
content. However, **actual words, punctuation, intentional verse omissions,
text-critical readings, theological distinctions, authored emphasis, note
texts, meaningful titles, paragraph/poetry divisions and reference labels can
carry meaning**. No rule may blindly strip or rewrite these. An apparent
editorial quirk must be classified as (a) purely presentational, (b) semantic/
textual, or (c) ambiguous. Normalize (a) by a **generic** reviewed rule,
preserve (b) unless an independently established correction is approved,
and hold (c) for explicit review rather than guessing. The project owner
determines substantial editorial changes.

- Keep an **exact before/after transformation manifest** (source hash, rule,
  affected elements, rationale, counts, reviewer, reverse mapping or rollback
  path); publish no silent textual/structural edits.
- Avoid one-off cleanups in the compiler or client; repair the curated source
  and regenerate.
- An official schema-compliant construct is not disposable just because a
  particular reader renders it poorly: distinguish data quality from a reader
  bug.

**Gate:** the curated OSIS/USFM is structurally valid, consistent with the
approved normalization rules and fully diffable from the untouched original.

## Phase 3 — Compare against a reliable witness

**Goal:** independently verify that cleaning did not change the **work**.

- Prefer an authoritative, independently obtained witness of the **same exact
  edition** (publisher OSIS/USFM, documented original, credible scanned print
  edition, or a separately source-pinned counterpart).
- Compare the **whole corpus**, not merely counts or sample chapters: words,
  punctuation, verse/key inventory, authored omissions, original text order,
  notes, semantic emphasis, introductions, poetry, titles and section scopes.
- Interpret differences by source edition and documented normalization rules:
  separate harmless serialization changes, reviewed presentation changes,
  source transcription defects, actual text differences and reader-only issues.
- A **different** edition can illuminate a problem, but cannot silently
  overwrite the chosen edition or prove exact-edition parity.
- Every discrepancy receives a classified disposition: preserve, corrected
  with evidence, or **blocked/explicitly unresolved**. Do not fabricate
  missing Scripture verses or restore content absent from the selected
  edition.

**Gate:** no unexplained loss, addition or change to the authorized edition's
substantive content; full-corpus comparison and accepted deltas have durable
receipts. If the authoritative witness is unavailable, clearly record
what could and could not be independently established.

## Phase 4 — Verify and correct references

**Goal:** machine-readable references that resolve accurately and retain
the source's intended meaning.

- Inventory every Bible reference, cross-reference, citation, commentary
  range, note target, introduction key and relevant implicit address.
- Check syntactic validity, **the source's own versification**, book/chapter/
  verse existence, range endpoints, destination semantics, duplicate/
  overlapping scopes, label–target agreement and source-internal linking.
- Correct malformed targets, broken ranges or mistaken book codes only after
  confirming the intended destination from the source or reliable witness.
  Preserve visible authored wording; a target-attribute repair is **not**
  permission to edit the author's label. Report each exact original/updated
  reference and reason.
- Keep commentary chapter-level and multi-verse annotations, and multiple
  sections with overlapping keys, without inventing aliases or suppressing
  paragraphs. Never manufacture verses omitted by a translation or move a
  note to an unsupported verse.
- Re-run source and reference checks after correction; log unresolved
  cases explicitly.

**Gate:** reference mapping is exhaustively checked; no unresolved
misdirected link is silently classified as working. Genuine source ambiguity
requires a documented editorial choice.

Reference repairs can reveal a new textual or structural discrepancy. In that
case, return to phases 2–3 and repeat the relevant full-source checks; the six
phases are ordered gates, not a ban on iterative corrections.

## Phase 5 — Compile SWORD and test in real readers

**Goal:** prove that the **final compiled artifact** faithfully represents
the approved source and works in independently maintained applications.

1. Compile from the curated OSIS/USFM with the matching documented SWORD
   importer (`osis2mod`, `usfm2mod` or an approved standard adapter).
   Pin importer/runtime versions, arguments, versification and `.conf`
   metadata. Prefer reproducible builds.
2. Independently re-read the **complete native SWORD**: text, Unicode,
   punctuation, ordering, addressable verse/entry keys, notes, references,
   introductions, headings, paragraph/poetry markup and boundary cases.
   Compare these to the curated source and approved deltas, not just to
   another copy of the compiled file.
3. Test the *exact candidate ZIP and module ID* in an isolated SWORD root
   with **diatheke**, then the established **real Xiphos test method**:
   install the module, open representative and edge-case passages,
   verify actual requested passage, rendered content, structure and long
   sections, introductions, parallel reading as relevant, and source
   reference labels/targets. Use actual link clicks **when possible** and
   verify where Xiphos displays the destination (sidebar versus main pane).
4. Where relevant, additionally test AndBible/JSword or another independent
   SWORD implementation. Report per reader **PASS / FAIL / INCONCLUSIVE /
   NOT TESTED**, with logs or screenshots identifying the final candidate.
   **Headless process startup is not GUI rendering proof; an unclicked
   hyperlink is not a clicked-navigation PASS.**
5. Distinguish actual compilation/data defects from individual reader
   rendering limitations. Fix the source/compiler, not the Bible application
   or an unrelated reader, when the data is wrong. Preserve real-reader
   evidence and regressions.

**Gate:** exact compiled source-to-native parity is documented, required
reader checks genuinely passed, and known limitations are identified.
A sampled Xiphos PASS does **not** imply every hyperlink was clicked.

## Phase 6 — Approve and publish

**Goal:** release a source-attested, reproducible and publicly verified edition.

- Require distinct recorded **rights**, **editorial** and **technical** approval.
  No green workflow can substitute for necessary human authorization.
- Commit the maintained source, allowed by its license, under
  `sources/cleaned/<resource-id>/`, along with its normalizer plans and
  provenance. If rights prevent public source retention, preserve it in
  controlled access storage and commit only non-sensitive provenance,
  receipts and permitted build inputs; **do not claim public reproducibility
  from files that the repository does not contain**.
- Commit the validated native SWORD payload and its source/native hashes,
  `metadata.json`, `EDITORIAL.md`, `SOURCE_VALIDATION.json`, release
  plan and exact catalogue snapshot. Package identity, version, rights,
  SWORD ID collision/replacement and rollback must be explicit.
- Execute tests, `scripts/validate.py`, deterministic
  `scripts/build.py`, native reader smoke, versioned release coverage
  and exact final ZIP SHA-256/size checks.
- Use **only** the existing `.github/workflows/pages.yml` publisher:
  first create/verify the **immutable GitHub Release**; then deploy
  the standard SWORD and JSON catalogue to GitHub Pages.
- Independently fetch the **live** catalogue and packages and compare
  full downloaded byte lengths/hashes. Close the tracking issue only after
  publication is actually verified.

**Gate:** source and transformation receipts retained, approvals granted,
published GitHub Release and Pages package accessible, and actual remote
checksum verification passed.

## Operational constraints and evidence

| Concern | Record / enforcement |
| --- | --- |
| Format | Real OSIS or USFM; third format only through approved standard adapter |
| Original | Immutable edition identity, origin URL, exact byte SHA-256 |
| Curated source | Standards-valid, generic cleanup rule, explicit reversible delta |
| Fidelity | Full-corpus source/witness comparison; exact exceptions reviewed |
| References | Exhaustive source/versification and label–target mapping audit |
| Output | Exact SWORD native readback, hashes and reproducible build contract |
| Xiphos | Real-reader install and representative GUI content/navigation evidence |
| Rights | Text and annotation redistribution/modification approval |
| Release | Official release-before-Pages workflow plus live-download checksum proof |

**Reuse first:** [Editorial rules](EDITORIAL_RULES.md),
[normalization contract](NORMALIZATION_POLICY.md),
[Bible onboarding](BIBLE_7_STAGE_WORKFLOW.md),
[commentary onboarding](COMMENTARY_7_STAGE_WORKFLOW.md),
[reader/parity lessons](RESOURCE_ONBOARDING_PLAYBOOK.md),
[publication gates](PUBLISHING.md),
[tool inventory](TOOL_REGISTRY.md).

Track implementation gaps in existing issues rather than promising that
every phase is already one-click automation: [#3](https://github.com/icfmp/Bible-Resources/issues/3)
(normalizer and reports), [#28](https://github.com/icfmp/Bible-Resources/issues/28)
(generic Bible source→SWORD parity), and
[#83](https://github.com/icfmp/Bible-Resources/issues/83)
(resumable fidelity checkpoints).

**Editorial rule of thumb:** normalize the encoding without mercy; never
normalize away the author's meaning.
