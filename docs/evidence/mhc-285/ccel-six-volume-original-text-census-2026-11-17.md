# MHC — six independently pinned CCEL volumes vs original CrossWire native text

**Date:** 2026-11-17  
**Scope:** private, read-only source/stock textual census; **not** edition equivalence, structural parity, publication, rights permission or editorial approval.  
**Issue:** [#285](https://github.com/icfmp/Bible-Resources/issues/285)  
**Draft PR:** [#286](https://github.com/icfmp/Bible-Resources/pull/286)  
**All six real original-source/native comparison jobs:** [GitHub Actions #44067734314](https://github.com/icfmp/Bible-Resources/actions/runs/44067734314), **SUCCESS** on feature revision `e7e91cfc246e8adbedcadba2883951e1f411df84`.  
**Independent general and original-native/JSword checks on the same revision:** [Validate #44067734326](https://github.com/icfmp/Bible-Resources/actions/runs/44067734326), [registry #44067734398](https://github.com/icfmp/Bible-Resources/actions/runs/44067734398), [native anchor #44067734343](https://github.com/icfmp/Bible-Resources/actions/runs/44067734343), [pinned JSword #44067734328](https://github.com/icfmp/Bible-Resources/actions/runs/44067734328), all **SUCCESS**.

## Exact original sources and boundaries

The six CCEL ThML/XML sources are **independently SHA-256-pinned** in the private intake manifest. Each matrix job acquires exactly one pinned source volume, the exact original official CrossWire MHC 2.2 ZIP (SHA-256 `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`), verifies full original native raw corpus SHA-256 `2c4fe82710165202fdec300ca9636a150a9998f19c7b19ee4e81db5a6b75f5b5`, checks original source section reference/body ordered SHA identities, then compares original **verse/range body Unicode** with actual pinned native K source starts.

The pipeline preserves all original source XML, references, authorial sections and commentary words. The **artifacts contain only controlled categories, counts, original file hashes, original line/reference hashes and reviewed XML tag names**—no XML, native binary, source word excerpt or unreviewed reader output. Each volume is an independent, reproducible checkpoint.

## Original section census (actual real SWORD comparison)

| CCEL volume | Original verse/range sections | Source/native difference **only in interior whitespace** | Different words or punctuation (further review, not source loss) | Original source start unoccupied in native K | Original adjacent divisions without visible text, preserved as structure | Explicit chapter reference markers followed by another `scripCom` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| I | 671 | 414 | 257 | 0 | 0 | 312 |
| II | 723 | 362 | 357 | 4 | 0 | 249 |
| III | 1,184 | 754 | 430 | 0 | 0 | 243 |
| IV | 695 | 228 | 466 | 0 | 1 | 249 |
| V | 405 | 367 | 38 | 0 | 0 | 89 |
| VI | 585 | 523 | 58 | 0 | 4 | 164 |
| **Total** | **4,263** | **2,648** | **1,606** | **4** | **5** | **1,306** |

**Internal invariants checked:** 2,648 + 1,606 + 4 + 5 = **4,263 source verse/range sections**; plus **1,306 chapter markers = 5,569** exact original CCEL `scripCom` annotations across all six original XML volumes. All markers are accounted for; this **does not certify full original structural/content parity**. The five divisions without visible words remain present in the SHA/order inventories and are separately recorded by original line/body hashes and child element name counts, not treated as lost commentary or silently removed.

All 1,306 original chapter markers in these witnesses are followed immediately by another `scripCom`, rather than the standalone `h2` or `p` expected by a legacy MHCC-only diagnostic. The standalone chapter-introduction comparison is **NOT TESTED**; original source metadata, narrative order and native chapter introduction parity remain for an independent structural audit. Strict legacy single-source tests are unchanged.

The four original source starts without an exact occupied native K address are in **volume II**, matching the known first-verse alias issue and CCEL digital reference mismatches tracked in [#290](https://github.com/icfmp/Bible-Resources/issues/290) and [#288](https://github.com/icfmp/Bible-Resources/issues/288). An absent *exact start index* is **not** evidence of missing authored prose; the full original word and index-only alias audit is separate.

## Priority for human textual and editorial review

The 1,606 `lexical_text_or_punctuation_difference` classes **do not assert 1,606 corrupted texts**. They need a further source-neutral and bounded distinction among punctuation, character forms, compilation headings/prefixes/suffixes, actual word selection/order and real omissions. Neither original CCEL nor its compiled CrossWire witness is automatically declared the definitive authorial print edition. No text is silently rewritten.

A separate **bounded** word-order/selection triage from this run contains **20** original-word order/selection attention cases and **46** alignment-budget-unresolved cases (volume subtotals: I 0/1; II 5/1; III 10/7; IV 0/2; V 2/18; VI 3/17). These are **not exhaustive counts of all original differences**, not a verdict of authored text loss and not a basis for correction without examining independently authenticated complete prose.

Important reader distinction: native CrossWire MHC already places the nine historically erroneous CCEL index references in the correct chapters/ranges where supported by actual source prose (issues [#288](https://github.com/icfmp/Bible-Resources/issues/288), [#289](https://github.com/icfmp/Bible-Resources/issues/289)); **do not copy CCEL's incorrect digital reference indices into the module**. The separate three source-authenticated index-only first-verse aliases preserve all original K/I/TOP entries; independent pinned JSword proves alias/master reader access, not Xiphos or Android GUI equivalence.

## Next independent gates (not passed yet)

1. Diagnose the **1,606** text/punctuation classes by approved reversible comparison methods; do not infer authorial omissions from compiler-added text.
2. Audit source-vs-stock **complete paragraph/poetry/headings/notes/reference ownership and section boundaries**, including the 1,306 non-standalone chapter markers and 5 non-visible source divisions.
3. Establish complete edition identity and source-level redistribution/derivative authorization, distinguishing CrossWire's module PD claim from CCEL's protected electronic-edition layers; seek editorial owner decision before any metadata correction.
4. Obtain real graphical corrected-candidate reader presentation and navigation evidence. Previous JSword is engine-only, not a GUI PASS.
5. Keep draft PR #286 **unmerged**, no catalogue/module publication or repository release without explicit owner authorization.

This source-bound receipt is metadata only. All original third-party texts and module binaries remained in private disposable runners.
