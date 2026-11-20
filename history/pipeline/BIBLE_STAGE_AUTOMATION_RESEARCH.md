# Bible stage automation — historical findings worth retaining

**Archive, not an operator manual.** This is the concise record of decisions learned while testing real USFX/OSIS/SWORD sources in November 2026. Consult the [current stage runner workflow](../../docs/workflows/BIBLE_STAGE_AUTOMATION.md), [single production contract](../../docs/PRODUCTION_PIPELINE.md) and [source/native technical guidance](../../docs/technical/README.md) for new work. The original 1,127-line investigation, including intermediate sample hashes and all experiments, is recoverable from Git history at pre-condensation commit `d17d41088eea269e879cbfe46f37a17779ea0ef9`.

## 1. Upstream changes must invalidate pinned inputs

The public WEBP upstream archives changed between 9 and 10 November 2026; their newly observed SHA-256s differed from the original intake manifest. The runner **correctly rejected** the changed bytes. The remedy is an independent read-only observation and a reviewed **new** source pin, never an automatic manifest update. [Observed private fingerprint run #42799441256](https://github.com/icfmp/Bible-Resources/actions/runs/42799441256).

## 2. A verse/paragraph count is not structural equivalence

Distinct audits are needed for actual native Scripture keys, main-text punctuation/word sequence, and paragraph/poetry **open and close positions**. A source/native pair can have identical event counts and order while moving a paragraph boundary several words. Compare book-relative word and nonwhitespace-character ordinals for the full pair, including crossed milestones, mixed `p` and `q` events and verse-zero structure.

Evidence/tools explored: `scripts/source_native_structure_topology.py`, `scripts/source_native_ordered_body.py`, `scripts/native_milestone_pair_audit.py`. Their existence does not by itself prove universal driver support.

## 3. Keep machine gates independent

The research stage 4/5 receipts distinguished four questions:

| Gate | Question | Insufficient substitute |
| --- | --- | --- |
| 4a | Native reference registry and occupied keys vs source identity | Comparing chapter counts |
| 4b | Main-text content in actual compiled entries | A 2-verse smoke test |
| 4c | Source/native paragraph and poetry boundary *positions* | Equal event totals |
| 4d / 5 | Note/annotation types, text, anchors and links | Same note count or `osisRef` attribute without tested destination |

A single `PASS` in one dimension **never** certifies the others. Source-to-SWORD migrations require separately proven versification, whole-source original/cleaned coverage and a complete native reader report.

## 4. Work within actual format/reader limits

- USFX `p` can compile to OSIS/SWORD `div type="x-p"`, and `q` to native line milestones. Similar visual appearance does **not** prove the same source structure.
- Original USFX/USFM and publisher OSIS may describe different revisions: do not import one format's paragraphs, notes, labels or verse identities into another without edition provenance.
- An original pre-chapter `p`, a book title and a native introductory `I` entry may have different ownership; never flatten them into verse 1.
- Native `RawText` and `zText` drivers need actual reader tests and bounded metadata-only diagnostics. Stable `diatheke` output is not a substitute for independent graphical reader acceptance.

## 5. Efficient, reproducible operation

One resource-specific intake manifest, pinned official schemas, no undisclosed source bytes in CI, and a **metadata-only source-hash-bound receipt** for each stage. Reuse successfully proved inputs rather than re-downloading or repeatedly compiling the same evidence. Preserve each finished issue/PR checkpoint so a later worker can resume without relying on chat history.

The old run book contained exploratory stage commands, test-fixture-specific findings and partially completed pilot status; **none are active release criteria today**. For unsupported constructs, return `BLOCKED`/`PARTIAL` rather than inventing data or claiming acceptance. New publication must follow the current rights, editorial, native and public-download release gates.
