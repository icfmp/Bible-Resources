# J. N. Darby — BPC 2024 rev. 2.0 / Bible Resources 0.1.0

**Release preparation (not yet published):** The project owner approved exactly eight reversible technical note destination corrections and conventional SWORD rendering on 2026-11-12 ([decision](https://github.com/icfmp/Bible-Resources/issues/133#issuecomment-6826689084)). Publication requires separately attested final binary and catalogue delivery.

## Original source and legal rights

- Official publisher: Bibles et Publications Chrétiennes (BPC).
- **Exact edition:** 2024 rev. 2.0, **Public Domain**, not the separately revised 2026 CC BY-NC-ND translation ([publisher listing](https://editeurbpc.com/telechargements)).
- Exact authorial OSIS SHA-256: `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`. Original file remains immutable and is not silently rewritten.
- This module is independently curated by Bible Resources; not an official BPC SWORD module.

## Verified, reversible changes to **machine** semantics only

- **Eight** reviewed contextual `osisRef` destination corrections, [full original→new target table](https://github.com/icfmp/Bible-Resources/issues/133#issuecomment-6825557703), each pinned to an unchanged original note host and text.
- **Three** printed references in text-critical notes describing intentionally absent verses (Matthew 23.14, Acts 8.37, Acts 15.34): preserve their authorial explanatory prose, but make their wrappers *plain text*, not misleading clickable targets. No verse was invented or restored.
- **Two** nonstandard inline measurement tags in the Ezekiel note become standard OSIS `seg type="x-measure"` tags. Authorial words, call letters, positions and all unedited source bytes remain unchanged.
- All changes are expressed as independent, testable, source-bound overlays in `scripts/repair_osis_*.py` and research manifests. The publisher original has never been overwritten.

## Preservation, fidelity and reader acceptance

- 66 Protestant books, **31,166 source-populated numbered verses**, **6,340 original notes**. All note bodies, caller letters and full lexical Bible text passed independent source/native comparisons. Marked paragraphs, poetry, headings and word-relative positions are audited; literal whitespace differs from the official source and printed pagination is not guaranteed.
- Actual independent SWORD/Xiphos and AndBible stable 5.1.1117 Android/JSword tests confirm representative French reading, source footnotes, deliberately absent verses and **real corrected Romans 16.25 → Colossians 2.2–3 navigation**. [Technical issue #62](https://github.com/icfmp/Bible-Resources/issues/62).
- The project’s separate GNOME Bible alpha is **not** an acceptance gate. No exhaustive per-note GUI or printed-facsimile claim.
- Any future publisher correction/revision is a **new source identity** to audit; upstream BPC error report remains a draft and no publisher reply has been claimed.

The stable release must use distinct SWORD module ID `BRJND2024`, `zText`, `Luther`, and version `0.1.0`, with the exact source-fidelity report, independent native indexed-key audit, schema report, final SWORD binary hashes, a real catalogue snapshot and successful Pages endpoint verification.
