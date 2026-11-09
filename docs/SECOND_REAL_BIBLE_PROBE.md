# Private second real Bible acceptance experiment: WEBP

Issue [#28](https://github.com/icfmp/Bible-Resources/issues/28) requires proving that the generic source/reader tools work on a **different actual Bible** rather than merely on synthetic fixtures or the LSG release.

**Second test edition:** eBible [World English Bible, Protestant-book selection (WEBP)](https://ebible.org/find/show.php?id=engwebp), which the publisher identifies as public domain. The publisher also identifies "World English Bible" as a trademark and requests that changed text not retain that product title. These public-domain and trademark statements **do not themselves approve any transformed release**.

### Original independent publisher inputs

- Official USFX source ZIP: https://ebible.org/Scriptures/engwebp_usfx.zip
- Official SWORD module ZIP: https://ebible.org/sword/zip/engweb2025peb.zip

These are *different artefact lineages*. Both are fetched read-only from the publisher for an isolated, ephemeral GitHub Actions job. Their **actual exact SHA-256** values are computed independently and attached to a metadata-only report. The workflow never commits, republishes, uploads, changes, or installs either Bible into the catalogue.

### Reproducible workflow

The optional GitHub Actions workflow **Review second real Bible (WEBP source and SWORD index)** can be dispatched manually. It also runs for the PR that introduces/changes its workflow or script.

The workflow:

1. Downloads the independently published USFX and original SWORD ZIPs over HTTPS, with no access credentials.
2. Validates safe paths/limits and reads actual original **USFX** books/chapter/verse openings and content fingerprint, without asserting that USFX is OSIS.
2a. Reports all original USFX book identifiers, including any **unnumbered introduction/front-matter books**, as authorial source evidence. Such books are not fabricated into missing verse IDs or silently discarded: their complete text/structure remains an explicit outstanding audit, and they are excluded only from numerical **diagnostics** against ordinary native Bible verse keys.
3. Installs only the independently acquired original provider ZIP into a **private temporary SWORD root** after a complete bounded archive inspection.
4. Compiles the existing generic native SWORD reader against the released system `libsword-dev`; enumerates **real native occupied verse keys**, installed chapter registry and distinct introduction slots. The test requires that this second real source uses `zText`, thereby exercising a different driver from the published LSG `RawText`.
5. Reports book/chapter/verse totals and source-vs-native ordinal count diagnostics; does **not** assume USFM/USFX book codes match OSIS names or that matching counts prove true index/content fidelity. An exact reviewed book mapping is still required for full authorial-reference parity.
6. Uploads **only a text-free JSON evidence file** with exact original-archive hashes and diagnostic counts. The upstream Biblical source and binary are **not** uploaded in any CI artefact.

### Observed first real run — 2026-11-09

A real run [#42711687348](https://github.com/icfmp/Bible-Resources/actions/runs/42711687348) **succeeded at independently inspecting the original source and the stock-SWORD reader**, using released `libsword` 1.9.0 and the eBible original `engweb2025peb` `zText` module (`Version=426.0`, `Versification=KJV`). It uploaded a private **metadata-only** audit receipt; the source archives themselves were never uploaded or published.

Independently collected, exact original archive SHA-256 values:

- WEBP USFX publisher ZIP: `66f99b22a380d8ef8dbd9d401806fc02be3650e5fe3dbb0cec4d9693b53e1e44`
- WEBP original SWORD ZIP: `53d45377d1aa376f483aded415b6d122b7cbe6795baddc49dae6574e304b8810`

**Critical edition/canon-scope discrepancy requiring editorial source review:** the original downloaded **USFX file contains 83 USFX book sections, 81 with numbered verses (38,071 distinct numbered verse markers)**; two are unnumbered `FRT` and `GLO` and must retain their authored introductions/glossary. The separately published original **SWORD zText reader exposes 66 books and 31,100 occupied ordinary native verse references**, plus 1,255 occupied verse-zero introduction records and two nonaddressable TOP records.

Those archive contents do **not** have an independently verified one-to-one book/canon and date/revision mapping. Their differing totals **cannot establish which specific verses or texts are missing**, nor imply that the official provider published incorrect Biblical text. The publisher's landing page describes the WEBP selection as omitting Deuterocanon; the actual downloaded authored USFX archive contains additional identified sections, so the source-to-compiled subset needs independent explicit canonical-book/edition mapping before any fidelity gate can call these two particular files equivalent. This is **not** an invitation to delete, fabricate or auto-convert any source content.

The research workflow now **pins both exact upstream ZIP SHA-256 values** above. If eBible changes either archive, the experiment blocks and requires a reviewed new baseline rather than silently treating changed publisher data as the same tested source. The report explicitly marks `source_to_sword_fidelity_gate=blocked_canon_scope_mismatch_requires_edition_review` when original numbered-book count differs from the native occupied-book count, and keeps `source_to_sword_exact_edition_identity_verified=false`, `source_verse_numbering_against_native_reader_verified=false` and all content/notes/rights/approval booleans `false`. This is a successful **independent real zText instrumentation trial**, not a completed #28 source-to-compiled audit.

### Canonical-book crosswalk versus the complete authorial source

The follow-up [standard USFM→SWORD native book-scope audit](SOURCE_NATIVE_BOOK_SCOPE.md) adds an **explicit source book-code mapping** for the standard 66 books. Instead of assuming that the ordinal 40th USFX book is the ordinal 40th native reader book after extra source books, it checks every mapped **chapter and verse identifier** by book code.

It preserves a separate enumerated list of **all additional authorial USFX books and their numbered verse counts**, including unnumbered `FRT` and `GLO`. It never silently removes or merges those sections. The experiment reports canonical-key parity or precise mismatched references as a **scoped index diagnostic**, while leaving complete source-to-compiled correspondence and literary/editorial equivalence **unverified**. Even an exact canonical key subset cannot justify treating the larger source as a proven edition-identical 66-book module.

### Remaining proof requirements

This private smoke can prove the generic native inventory works on a different real module, and can audit the independent original authorial USFX file. **It cannot** certify exact original USFM/USFX → OSIS conversion, note/word/Strong/reference/structure preservation in a compiled module, an Xiphos/AndBible frontend, an approved source version, redistribution of modified text, or another published resource.

The workflow is excluded from everyday repository Validate to prevent an external publisher outage from blocking routine code reviews. Network failures and source changes are independently recorded; after successful first execution, its actual SHA-256 baselines must be reviewed before treating a later upstream download as the same revision.

No second Bible is published by this workflow. No changes to the released LSG 0.1.0 source or SWORD files are authorized or made.
