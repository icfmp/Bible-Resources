# Louis Segond 1910 — Bible Resources 1.0.2

This update restores **803 original chapter-opening section headings** to numbered verse 1 entries of the SWORD module, including Rom 1 « Adresse et salutation » and Rom 2 « Les païens ». Each source-authored title is marked with OSIS-valid type=x-section, enabling the standard compiler to store it as a pre-verse heading instead of inaccessible chapter-intro material. No title words, verses, notes, cross-references or original source material were added or removed.

Full native SWORD comparison: original 31,170 numbered verse IDs retained, 31,169 populated native Scripture texts and 9,751 notes unchanged; all 803 headings found at their authorial first verse. Xiphos is the owner's provisional reference reader; a screenshot from Bible prompted this correction but the app itself was untouched.

Known limitations are unchanged: the stock Segond versification merges original Mark 10:53 into the Mark 10:52 native slot; explicitly enabling SWORD cross-references can expose note XML in some plain-text clients (issue #549). The previous 0.1.0, 1.0.0 and 1.0.1 release assets remain immutable; eBible fraLSG is public domain.

## Actual-reader multi-book acceptance evidence (2026-11-24)

- **Reviewed, non-public candidate:** PR #551, CI commit `d5852193058db6678994e9d1ea388e81171787f5`.
- [Real Xiphos 16-book run #45334886553](https://github.com/icfmp/Bible-Resources/actions/runs/45334886553) — **passed**. The independent Ubuntu 24.04 Xiphos GTK process ran under a disposable X11 display, opened actual references via Ctrl+L and copied authorial Bible pane content; neither artificial text rendering nor merely detecting a window was counted as title proof.
- **16/16** sampled chapters had **exactly one standalone copyable heading line** matching the unmodified authored title from the precise 1.0.2 source; **16/16** also had an independent 16-consecutive-word native `diatheke` SWORD chapter witness. A short first verse does not constitute a reader failure: the independent chapter witness supplements, but never replaces, the already proven all-verse full native check.
- **Old Testament (8/8):** Gen.1.1, Exod.1.1, Josh.1.1, Ps.1.1, Isa.2.1, Ezek.1.1, Hos.1.1, Hag.1.1.
- **New Testament (8/8):** Matt.1.1, Mark.1.1, Luke.1.1, John.1.1, Acts.1.1, Rom.1.1, 1Cor.1.1, Rev.1.1.
- Each book was selected from the **803 original source-authored first-title sites** using deterministic canonical strata; untitled chapters or books with no applicable newly typed chapter-first title are not misreported as missing headings. The two originally reported Rom.1.1 and Rom.2.1 cases separately passed [reader run #45280288257](https://github.com/icfmp/Bible-Resources/actions/runs/45280288257).
- [Native source/title/verse/note QA run #45334886453](https://github.com/icfmp/Bible-Resources/actions/runs/45334886453): all **803/803** source-attested opening titles present in numbered first native verse entries, **31,169** occupied Bible native entries and **9,751** notes preserved; all six compiled native member hashes match the independently regenerated candidate. This is corpus-wide native evidence, separate from the focused 16-chapter GUI sample.
- On the exact CI commit above, **all eight** workflows passed: Validate, architecture guardrails, tool registry, note rendering, reproducible SWORD build, structural reference comparison, full chapter-first-title native audit, and actual Xiphos GUI sample.
- **Unproven:** pixel-level layout of every heading in every graphical reader, BibleTime or AndBible behavior, and public release/download availability. These are not implied by this test.

**Release decision:** this remains an **unpublished 1.0.2 candidate**. Owner publication approval and a separate controlled merge/release-before-Pages/public-HTTPS verification remain required. Do not change the application repository `icfmp/Bible` or overwrite historic releases.
