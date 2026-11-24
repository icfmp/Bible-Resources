# Louis Segond 1910 — Bible Resources 1.0.2

This update restores **803 original chapter-opening section headings** to numbered verse 1 entries of the SWORD module, including Rom 1 « Adresse et salutation » and Rom 2 « Les païens ». Each source-authored title is marked with OSIS-valid type=x-section, enabling the standard compiler to store it as a pre-verse heading instead of inaccessible chapter-intro material. No title words, verses, notes, cross-references or original source material were added or removed.

Full native SWORD comparison: original 31,170 numbered verse IDs retained, 31,169 populated native Scripture texts and 9,751 notes unchanged; all 803 headings found at their authorial first verse. Xiphos is the owner's provisional reference reader; a screenshot from Bible prompted this correction but the app itself was untouched.

Known limitations are unchanged: the stock Segond versification merges original Mark 10:53 into the Mark 10:52 native slot; explicitly enabling SWORD cross-references can expose note XML in some plain-text clients (issue #549). The previous 0.1.0, 1.0.0 and 1.0.1 release assets remain immutable; eBible fraLSG is public domain.

## Actual-reader multi-book acceptance evidence (2026-11-24)

- **Pre-publication reviewed candidate (now released):** PR #551, CI commit `d5852193058db6678994e9d1ea388e81171787f5`.
- [Real Xiphos 16-book run #45334886553](https://github.com/icfmp/Bible-Resources/actions/runs/45334886553) — **passed**. The independent Ubuntu 24.04 Xiphos GTK process ran under a disposable X11 display, opened actual references via Ctrl+L and copied authorial Bible pane content; neither artificial text rendering nor merely detecting a window was counted as title proof.
- **16/16** sampled chapters had **exactly one standalone copyable heading line** matching the unmodified authored title from the precise 1.0.2 source; **16/16** also had an independent 16-consecutive-word native `diatheke` SWORD chapter witness. A short first verse does not constitute a reader failure: the independent chapter witness supplements, but never replaces, the already proven all-verse full native check.
- **Old Testament (8/8):** Gen.1.1, Exod.1.1, Josh.1.1, Ps.1.1, Isa.2.1, Ezek.1.1, Hos.1.1, Hag.1.1.
- **New Testament (8/8):** Matt.1.1, Mark.1.1, Luke.1.1, John.1.1, Acts.1.1, Rom.1.1, 1Cor.1.1, Rev.1.1.
- Each book was selected from the **803 original source-authored first-title sites** using deterministic canonical strata; untitled chapters or books with no applicable newly typed chapter-first title are not misreported as missing headings. The two originally reported Rom.1.1 and Rom.2.1 cases separately passed [reader run #45280288257](https://github.com/icfmp/Bible-Resources/actions/runs/45280288257).
- [Native source/title/verse/note QA run #45334886453](https://github.com/icfmp/Bible-Resources/actions/runs/45334886453): all **803/803** source-attested opening titles present in numbered first native verse entries, **31,169** occupied Bible native entries and **9,751** notes preserved; all six compiled native member hashes match the independently regenerated candidate. This is corpus-wide native evidence, separate from the focused 16-chapter GUI sample.
- On the exact CI commit above, **all eight** workflows passed: Validate, architecture guardrails, tool registry, note rendering, reproducible SWORD build, structural reference comparison, full chapter-first-title native audit, and actual Xiphos GUI sample.
- **Unproven by these reader tests:** pixel-level layout of every heading in every graphical reader and BibleTime or AndBible behavior. Public release/download availability was verified separately by the official publisher, below.

## Publication receipt — 2026-11-24

**Status: publicly released and live catalogue verified.** The owner's instruction to continue after complete technical signoff authorized the release workflow; approval for publication was distinct from the technical CI result. Source metadata and historic published versions were preserved.

- **Approved PR:** [#551](https://github.com/icfmp/Bible-Resources/pull/551), merged in `main` as commit `7092d6e9318eeff46081feb831c207efa5859af2` after all eight CI workflows passed on reviewed candidate HEAD `2e419eae770ba7d0f7e6571b607f9931ee6c8716`.
- **Single authorized release publisher:** [GitHub Actions run #45339868788](https://github.com/icfmp/Bible-Resources/actions/runs/45339868788), **success**. It revalidated sources and tests, built the deterministic SWORD distribution, required release-plan coverage for all approved modules, created or verified versioned GitHub Release assets **before** deploying Pages, and independently checked all five advertised live HTTPS ZIP downloads.
- **Public tagged release:** [`lsg-1.0.2`](https://github.com/icfmp/Bible-Resources/releases/tag/lsg-1.0.2), targeting `7092d6e9318eeff46081feb831c207efa5859af2` (published 2026-11-24 06:22:17 UTC).
- **Versioned asset:** [`BRLSG1910-1.0.2.zip`](https://github.com/icfmp/Bible-Resources/releases/download/lsg-1.0.2/BRLSG1910-1.0.2.zip), exactly **4,268,030 bytes**, SHA-256 `547d5b953c3a3720bf21bed0e48d515e1d9c581dc419bd4b0af5593286180f01`. The GitHub Release provides `RELEASE_PROVENANCE.json`, `SOURCE_VALIDATION.json` and `SHA256SUMS.txt`.
- **Live public catalogue:** https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json ; **live advertised SWORD package:** https://icfmp.github.io/Bible-Resources/sword/packages/BRLSG1910.zip . The publication workflow's **successful** `verify_public_catalogue.py` step independently downloaded and SHA-256-checked the complete live ZIP files for `BRJND2024`, `HMCCModern`, `BRLSG1910`, `MHC` and `MHCC`. Public Pages package URL is the current unversioned download entry; distinguish it from the immutable versioned GitHub Release asset.
- **Source and content identities:** cleaned OSIS SHA-256 `2b8342a67d8e97b433670450fe9dd9e58917a7fcfc0cb4d321882ca8219dc3bd`. All **803** original chapter-first section headings verified in native verse 1; **31,169** populated native Scripture bodies and **9,751** source notes retained; 16/16 source-stratified real Xiphos GUI samples passed. No authorial title text or Scripture text was invented or modified.
- **Rights:** public-domain eBible `fraLSG` source as documented by https://ebible.org/fraLSG/copyright.htm; the module retains original source and editorial provenance.
- **Unchanged known limitations:** `Segond` native registry combines original Mark 10:53 into Mark 10:52; no source-absent Job 34:37 was added; cross-reference/plain-text rendering issue #549 is separate. BibleTime and AndBible have not been newly accepted by this release's GUI sample.
- **Historical integrity:** no change to released `0.1.0`, `1.0.0`, or `1.0.1` artifacts. The `icfmp/Bible` application repository was not modified.

Publication verification does **not** certify a complete pixel-level visual inspection of all 803 headings or a printed-1910 typography collation. Any new reader regression must receive its own source-verified issue and correction, not a silent modification to this tagged release.

