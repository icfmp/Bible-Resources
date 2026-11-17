# MHC — source/stock lexical subtype triage for all six original volumes

**Date:** 2026-11-17  
**Project:** [Issue #285](https://github.com/icfmp/Bible-Resources/issues/285), [draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286)  
**Actual original-source/native audit:** [GitHub Actions #44068890903](https://github.com/icfmp/Bible-Resources/actions/runs/44068890903), all six independent CCEL volumes **SUCCESS** at source head `610a08c2d0bf72f0809906e63bfff6a29d990ef2`.  
**Prior full section census:** [ccel-six-volume-original-text-census-2026-11-17.md](ccel-six-volume-original-text-census-2026-11-17.md), [Actions #44067734314](https://github.com/icfmp/Bible-Resources/actions/runs/44067734314).

## Exact subtype reconciliation

All **1,606** sections whose original visible source-body comparison was broadly classified as `lexical_text_or_punctuation_difference` now have a separate original lexical subtype. Original CCEL data and CrossWire original stock were individually SHA-pinned and inspected privately, with **only closed class counts** exported.

| CCEL volume | Same exact Unicode word tokens, punctuation/nonword differences | Full source whitespace-normalized text occurs within longer stock text | Full stock whitespace-normalized text occurs within longer source | Actually different Unicode word token sequences/selections | Total broad difference class |
| --- | ---: | ---: | ---: | ---: | ---: |
| I | 243 | 5 | 1 | 8 | 257 |
| II | 332 | 11 | 1 | 13 | 357 |
| III | 192 | 58 | 37 | 143 | 430 |
| IV | 442 | 9 | 0 | 15 | 466 |
| V | 4 | 5 | 0 | 29 | 38 |
| VI | 9 | 22 | 0 | 27 | 58 |
| **Total** | **1,222** | **110** | **39** | **235** | **1,606** |

The **235** different-word-sequence cases subdivide as follows, independently counted:

| Original/stock word-token relationship | Cases | Meaning / limitation |
| --- | ---: | --- |
| Source words contiguous inside longer stock | 21 | Original words found; stock adds tokens around them; **not** proof identical punctuation or markup |
| Source words in original order with extra stock words | 1 | All source words found in order; not exact original division |
| Stock words contiguous inside longer source | 3 | Possible source content not represented in same stock slot; check neighboring slots or edition |
| Stock words in order with extra source words | 128 | Source has extra words relative to this stock slot; **not automatically 128 omissions** |
| Different word order or selection requiring further review | 82 | Could be historical edition difference, punctuation/tokenization, wrong reference join, or genuinely absent text; no automatic edit |
| **Total** | **235** | **Research-only** |

The most striking source-longer-than-stock group is **volume III**, with **117 of the 128** `stock_words_in_order_with_extra_source_words` cases; further examination must not infer missing text from a single address since SWORD can repeat or aggregate native blocks and CCEL editorial sections may differ from the prepared module.

### Punctuation-only subtype distinction

Of **1,222** cases with the **same exact Unicode word tokens**, there are **1,186** with the same nonword symbols but different locations/whitespace, **35** with different nonword character identities/counts, and **1** with the same nonword symbol counts but different order. Even identical word sequences are **not** proof of punctuation, Bible quotations or annotated-reference fidelity.

## Canonical-book localization — independent final source-book reconciliation

[Six real source-book relationship audits #44070922738](https://github.com/icfmp/Bible-Resources/actions/runs/44070922738) **all SUCCESS**, at draft PR head `0b462154351320763efa3eca6a22be3aa5e64bfd`. The generic private comparator now aggregates the *original source reference's book code*, not a book guessed from stock prose, and the workflow independently asserts that the per-book counts sum exactly to each of the prior closed lexical classes. No original words, body fragments or unreviewed editorial headings are exported.

The **128** cases where original CCEL has extra words relative to the native CrossWire entry *at the same start reference* localize exactly as:

| Original biblical book | Source-longer-than-stock in-order cases |
| --- | ---: |
| **Psalms (Ps)** | **116** |
| Isaiah (Isa) | 3 |
| Romans (Rom) | 3 |
| Acts | 2 |
| Genesis (Gen) | 1 |
| 2 Chronicles (2Chr) | 1 |
| Ecclesiastes (Eccl) | 1 |
| Jeremiah (Jer) | 1 |
| **Total** | **128** |

**Priority for editorial/source-native investigation:** Psalms accounts for **116/128** of this precise relationship class. It is a systematic *same-start stock-versus-source text-scope discrepancy*, but the current evidence does **not** distinguish compiled verse-group sharing, source division ownership, altered historical edition, omitted words or prepared digital headings. Do **not** bulk-copy CCEL paragraphs or mechanically split/merge the SWORD commentary to resolve these counts. The authored text and canonical locations must be authenticated before judging each case. Psalms should be audited as a reusable pattern before reviewing the smaller independent classes.

The separate **82** cases requiring different word-order/selection examination concentrate in **Matthew (13)**, **John (10)**, **Proverbs (9)**, **Acts (6)**, **2 Chronicles (5)**, **Psalms (5)** and **Romans (5)**; other original books account for the remaining **29**. These **82 broad relationship cases** are not the same metric as the **20** bounded definite-LCS original-word-order differences or the **46** LCS-budget-unresolved results noted above.

The independent canonical-book reference is just research metadata, not a source verse reassignment. All six audited original source sections and native original content remain intact.

## Linear order-only check for oversized word alignments

The previous 46 over-budget original **nonlink-prose** alignments used a quadratic-cost longest common subsequence (LCS) gate and could not report a numerical mismatch. A new **generic** exact Unicode case-sensitive linear subsequence check (max 100,000 word tokens per side; no original words emitted) tests only whether *all original nonlinked source words* occur **in the same order** inside the original CrossWire native entry selected by the original source start.

All six original text comparison jobs in [GitHub Actions #44071936525](https://github.com/icfmp/Bible-Resources/actions/runs/44071936525) **SUCCEEDED**, plus full [Validate #44071936541](https://github.com/icfmp/Bible-Resources/actions/runs/44071936541) and [tool registry #44071936516](https://github.com/icfmp/Bible-Resources/actions/runs/44071936516). Real SHA-pinned exact source and stock original editions remain unchanged.

| CCEL volume | Previously LCS over budget; now independently checked for full in-order original source word containment | Shorter exact LCS source word-order review cases |
| --- | ---: | ---: |
| I | 1 | 0 |
| II | 1 | 5 |
| III | 7 | 10 |
| IV | 2 | 0 |
| V | 18 | 2 |
| VI | 17 | 3 |
| **Total** | **46** | **20** |

All **46** oversized cases had **`over_budget_source_order_not_proven`**: none contained **all** original nonlink-prose tokens in their original order *within the original same-start stock entry* under this exact linear test. **Zero** exceeded the separate 100,000-token linear processing limit. The other 20 cases already had a bounded exact LCS identifying at least one original word-order difference. Thus **66** cases have an explicit **same-start, original-nonlink-word ordering discrepancy**, not necessarily absent prose, wrong canonical keys, or a corrupted CrossWire prepared edition. Remaining 16 of the broad 82 unresolved original word comparisons were not in these attention classes and must not be conflated with the 66.

**This is a deliberately narrow negative witness:** finding no complete ordered subsequence in *one* native stock entry does **not** show the original authored text was lost. Reordering, separate linked Bible reference labels, different commentary edition/source scope, a neighboring native entry, or shared compiled raw blocks could account for the result. The exact LCS mismatch *magnitude* for these 46 is **still unavailable**; no case was declared word-for-word/markup/authorial parity. A careful private cross-slot/source-bound follow-up is necessary before any editorial change.

## Further gates

The previous SHA-pinned full six-volume census already accounted for all **4,263** original verse/range section markers and **1,306** separate chapter markers (5,569 total `scripCom`). The subsequent detailed lexical comparison is **a classification of the 1,606**, **not** a claim that the other 2,648 whitespace-only cases or the 5 nonvisible source divisions have complete markup/section/edition parity. The four unoccupied original source starts remain under the previously classified CCEL index / source-grounded alias issues #288 and #290.

The bounded separate nonlink-word alignment remains incomplete for **20** source order/selection cases plus **46** original sections exceeding the LCS resource budget. Those should be independently reviewed using explicit exact-source/stock provenance, with any efficient order-only check labelled **not a full word-order difference magnitude or textual identity result**. Inspect cases in volume III first for source/compiled edition differences, then volumes V and VI for oversize alignments.

**No authorial source XML, original CrossWire binary, original scriptural reference, published commentary module or catalogue entry was modified.** The PR remains **draft**. Real corrected-candidate Xiphos/AndBible GUI acceptance, complete source/stock authorial word+punctuation+markup+division parity, copyright permissions and editorial approval remain **OPEN**.

## Full original-source versus genuine native K-run scope census (2026-11-17)

The [six SHA-pinned private CI volume checks #44076596449](https://github.com/icfmp/Bible-Resources/actions/runs/44076596449) **all PASSED** on the unchanged CrossWire MHC 2.2 original and independently pinned original CCEL volumes, after adding a **source-neutral reuse** of the existing `NativeRawRunBoundaryInventory.report` in independently reconciled 20-case batches. Same revision: [Validate #44076596350](https://github.com/icfmp/Bible-Resources/actions/runs/44076596350), [generated tool registry #44076596299](https://github.com/icfmp/Bible-Resources/actions/runs/44076596299), [native stock audit #44076596269](https://github.com/icfmp/Bible-Resources/actions/runs/44076596269), [original source reference anchors #44076596386](https://github.com/icfmp/Bible-Resources/actions/runs/44076596386), and [pinned AndBible JSword #44076596359](https://github.com/icfmp/Bible-Resources/actions/runs/44076596359) also **PASSED**.

Every original CCEL verse/range section previously identified as `stock_words_in_order_with_extra_source_words` was reidentified by its original CCEL XML line, full source reference SHA-256, original body SHA-256 and exact same-start native raw SHA-256. The generic native inspector independently verified the *actual occupied* SWORD K keys, contiguous shared-raw run, the source's declared verse range and its authentic adjacent XML boundary. Every subset, source book, native reference digest and original full raw corpus was reconciled; **no authored text or native bytes were copied, rewritten or published**.

| CCEL original volume | Original book(s) | Source-longer same-start cases | Native raw K occupied-key extent equals original declared source range |
| --- | --- | ---: | ---: |
| I | Genesis | 1 | 1 |
| II | 2 Chronicles | 1 | 1 |
| III | **Psalms 116**, Ecclesiastes 1 | **117** | **117** |
| IV | Isaiah 3, Jeremiah 1 | 4 | 4 |
| V | None | 0 | 0 |
| VI | Romans 3, Acts 2 | 5 | 5 |
| **All volumes** | | **128** | **128** |

This is a **negative finding about a single suspected cause**: for this precise set of 128 source-extra-word cases (including all **116 Psalms**), mismatched *occupied K verse-range boundaries* are **not** an adequate explanation. It does **not** prove that the longer original prose is missing from the entire compiled MHC, that every authorial paragraph belongs in the native K payload, that electronic editions are identical, or that the source's XML section divisions are correctly encoded. The original native K raw repetition is independently observed, but is not itself authorial evidence of a section's intended prose.

**Next bounded research gate:** independently classify the **actual CCEL-only word spans** against the original ThML `scripRef` label ownership, neighboring authorial units and the original native intro/other distinct K payloads; distinguish scripture quote labels, embedded book/chapter headings, markup/editorial annotations, intentional digital-edition variants and possible genuine omissions. Do not infer from same-start text or equal occupied ranges that any historical authorial word was dropped. Only prepare corrections after provenance, printed/independent authorial witness, rights and real-reader checks; retain draft #286 and never alter the published catalogue without explicit approval.


## Whole six-volume exact source-extra word-gap topology (2026-11-17)

The new [six SHA-pinned original CCEL volume jobs #44084387688](https://github.com/icfmp/Bible-Resources/actions/runs/44084387688) **all PASSED** against the original complete, unchanged CrossWire MHC 2.2. The [full Validate run #44084387907](https://github.com/icfmp/Bible-Resources/actions/runs/44084387907), [tool registry #44084387698](https://github.com/icfmp/Bible-Resources/actions/runs/44084387698), [original full native stock #44084387857](https://github.com/icfmp/Bible-Resources/actions/runs/44084387857) and [pinned JSword #44084387677](https://github.com/icfmp/Bible-Resources/actions/runs/44084387677) independently passed on the exact same source commit `6c69a24037807f6334da459e40b9729fdbc4519e`.

Every reported word is compared **after removing only actual source ThML `scripRef` labels and independently parsed actual native `reference` labels**. Both forward-earliest and reverse-latest exact case-sensitive Unicode subsequence alignments are calculated. Only when those positions agree is the location and span count of original extra **unlinked** words called *unambiguous*. Otherwise the result is explicitly indeterminate. The report never exposes text, word tokens, XML or SWORD content.

| Original CCEL volume | Strictly unique alignment with only internal original extra words | Ambiguous repeated-word subsequence alignment | Original-source-longer same-start cases outside these two classes |
| --- | ---: | ---: | ---: |
| I | 1 | 0 | 0 |
| II | 0 | 0 | 1 (the genuine unlinked word sequences match after link-label removal) |
| III | 113 | 3 | 1 (unlinked word order/selection unresolved) |
| IV | 3 | 1 | 0 |
| V | 0 | 0 | 0 |
| VI | 3 | 0 | 2 (unlinked word order/selection unresolved) |
| **Total** | **120** | **4** | **4** |

The **128/128** original same-start source-longer relationship census therefore reconciles as **124 ordered unlinked source-extra cases**, **one actual unlinked-word equality after label removal**, and **three other unlinked order/selection cases**. The 124 source-extra cases comprise **120 uniquely interior** and **four ambiguous positions**; *none* is a certified authorial omission or source-edition corruption.

### Focus: all 116 original Psalms source-longer cases

- **112** have one or more **uniquely localized interior extra-word spans**, **three** have multiple exact subsequence alignments, and **one** has original-vs-stock unlinked word order/selection unresolved.
- Of the 112 uniquely localized cases, **111 have exactly one extra-word span** and **one has exactly two**.
- **97/112** have **at most 12** extra original unlinked word tokens, **106/112** at most 20, and **111/112** at most 40.
- The single largest anomaly has **585 extra source unlinked words** distributed into **two interior spans** (longest one: 569 words). It is bound to original CCEL Volume III **XML source line 27749**, original full reference SHA-256 `f9a402dda0436aaed29b311707a672f1057df6e7bba16b58a43e5a1a91ac56a0`, original body SHA-256 `48809f08f932d9d68c4cbc56267a6ffdf973bf9bbafc9401d0916296824fb4ea`, and authentic original native K raw SHA-256 `77f3d7bf9699b9cafadceabb62c8b192f554e485d997c85293666f38aa210ac4`. **This is a prioritized exact original-source witness, not permission to copy prose into the prepared module.**

The metadata-only per-volume ZIP receipts were uploaded by that run. All numbers above are directly reconciled from the original source-bound receipts, not an estimate from screenshots, headings, or textual excerpts.

**Next research gate:** distinguish these uniquely localized extra spans against the **actual adjacent original ThML authored division(s)** and **other original occupied native K/I payloads**, especially the 585-word outlier, before deciding whether the cause is structure, transformed references/markup, edition variation or an omission. Even a match in another native key is a textual location witness, **not** proof of correct authorial attribution. Verify source and legal ownership of any prospective correction. No original book/chapter/verse key, exposition, raw SWORD bytes or public resource has been edited. Draft PR #286 remains unmerged.


## Exact complete long source-extra span checks in genuine other same-chapter native keys (2026-11-17)

All SIX source-bound, complete, original CCEL-versus-CrossWire text jobs [#44087402684](https://github.com/icfmp/Bible-Resources/actions/runs/44087402684) **SUCCESS** at original research commit `eb7d00afec4ecb00cac066cc8be34fbb64e63bfe`. Independent same-revision checks **SUCCESS**: [Validate #44087402508](https://github.com/icfmp/Bible-Resources/actions/runs/44087402508), [tool registry #44087402563](https://github.com/icfmp/Bible-Resources/actions/runs/44087402563), [full native raw #44087402614](https://github.com/icfmp/Bible-Resources/actions/runs/44087402614), [reference anchors #44087402674](https://github.com/icfmp/Bible-Resources/actions/runs/44087402674), [pinned JSword #44087402527](https://github.com/icfmp/Bible-Resources/actions/runs/44087402527) and [Xiphos private startup/integrity #44087402780](https://github.com/icfmp/Bible-Resources/actions/runs/44087402780). **The Xiphos workflow is still NOT a real commentary-pane prose/navigation/whole-chapter GUI acceptance.**

The source-neutral, independently tested `OriginalExtraGapNativeChapterProbe` reuses the already attested **full 32,355-entry original stock raw replay**, not a new source or guessed copy. For each uniquely located source-extra **non-scripture-link** word difference of **at least 100 words**, it privately takes the original exact full extra spans (only those of **at least six words**), tests for **exact contiguous whole-token** occurrence in genuine different raw K/I payloads **of the same chapter**, and keeps only line/full-reference/body/native SHA-256, counts and closed labels. Repeated native K keys pointing at the **same raw payload** are counted but do **not** count as an independent textual witness. All six volumes were exhaustively classified for this threshold: **two** eligible source-extra outliers, one in III and one in VI; volumes I, II, IV and V each had **zero**.

| Original source volume and book | Original SHA-bound source position | Unique original extra unlinked word spans | Distinct other original native K/I raw payloads searched in same chapter | Exact whole-span matches in other K/I payloads | Selected raw duplicate native keys (not independent) |
| --- | --- | --- | --- | --- | ---: |
| III — Psalms | XML line **27749**; source ref SHA `f9a402dda0436aaed29b311707a672f1057df6e7bba16b58a43e5a1a91ac56a0`; body SHA `48809f08f932d9d68c4cbc56267a6ffdf973bf9bbafc9401d0916296824fb4ea` | **16 + 569 = 585** | K: **1**, I: **1** | **0/2** spans | **9** |
| VI — Acts | XML line **23188**; source ref SHA `f00b1d632a701e2617522eb9e214b3f6fa6b6547bbe836814a214636556ba06d`; body SHA `0d3f52a0c7cb4c29694995ecd920d3f4e1f95409e22df3f4025afbe12b51fb7d` | **235** | K: **4**, I: **1** | **0/1** span | **10** |

The exact native stock payloads independently linked by these two witnesses were SHA `77f3d7bf9699b9cafadceabb62c8b192f554e485d997c85293666f38aa210ac4` (Psalms) and `eec29229b36ef7affda5dd8babfeb3c3417965058392bb2451798a90fb499db4` (Acts). The **negative** result is narrowly meaningful: neither **full contiguous** original extra passage is copied verbatim into a *distinct* original K/I raw payload in that **same native chapter**. It does **not** rule out a partial match, a quotation fragment, location in another chapter/book, older/newer editorial edition differences, or different authorial section ownership. It does **not** prove actual omission of Matthew Henry's text from the **whole** CrossWire module.

**Next check:** privately inspect the original CCEL ThML element/paragraph/section boundaries immediately around these exact source positions, and independently compare against another authenticated textual edition of the full historical MHC; determine whether the 585/235 source-only passages are part of original exposition, a different digital preparation, or a misplaced division. Continue only reversible, source-pinned index/metadata work until human editorial choice and edition-level rights have been settled. No authorial words, XML, original module, native verse/alias key, compiled commentary, published catalogue or release were changed. Draft PR #286 remains unmerged.
