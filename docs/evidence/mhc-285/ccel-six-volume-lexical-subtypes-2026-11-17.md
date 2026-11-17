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


## Verified source-paragraph topology at the two high-impact CCEL original references (2026-11-17)

**All six original pinned source-volume text jobs [#44091627764](https://github.com/icfmp/Bible-Resources/actions/runs/44091627764) PASSED**: the original ThML `scripCom` line/full-reference SHA and its **immediately following actual `div`** were strictly reparsed with entities/network disabled; original `div` Unicode text and inline `scripRef` token positions matched the independent original full-source census. Every exact source-only nonlinked gap was reconciled with original `p` character boundaries in **the authentic source bytes**, not a synthesized source/stock section. A second **6/6 PASS** [#44092560744](https://github.com/icfmp/Bible-Resources/actions/runs/44092560744) safely reports only each source's own original `scripCom` Bible citation claim, validated against its full original SHA; this is **not** a correction or an authenticated stock-native verse assignment.

| Source and original claimed reference | Exact source section | Extra prose not in same-start native K raw | Actual original ThML paragraph ownership | Adjacent original source boundary |
| --- | --- | --- | --- | --- |
| **CCEL III — `Bible:Ps.7.1-Ps.7.9`** | Original XML line **27749**, body SHA `48809f08f932d9d68c4cbc56267a6ffdf973bf9bbafc9401d0916296824fb4ea`; **14** source `p` elements / **2,503** unlinked words | **16 and 569** extra unlinked words in **two exact word intervals** | **Each interval covers 100% of a distinct original `p`**; no partial paragraph, paragraph-spanning word or out-of-`p` word. The other selected K raw lacks both, and the entire other *same-chapter distinct* K/I raw search found **0/2 complete-span matches** | Exactly next source sibling is another `scripCom` |
| **CCEL VI — `Bible:Acts.17.22-Acts.17.31`** | Original XML line **23188**, body SHA `0d3f52a0c7cb4c29694995ecd920d3f4e1f95409e22df3f4025afbe12b51fb7d`; **22** source `p` elements / **6,145** unlinked words | **235** extra unlinked words in one exact interval | **The interval covers 100% of one original `p`**; no partial paragraph, paragraph-spanning word or out-of-`p` word. The other selected K raw lacks it, and the other *same-chapter distinct* K/I raw search found **0/1 complete-span matches** | Exactly next source sibling is another `scripCom` |

This establishes a **source-digital-paragraph-level difference at two original same-start SWORD entries**, far stronger than an arbitrary missing-word fragment. However these three `p` elements could be **historical commentary prose, Bible verse quotations, ancillary editorial material, or content prepared/attributed differently in other editions**. None can yet be labelled a proven *Matthew Henry authorial omission*, a missing native comment elsewhere in CrossWire, or a license to alter the original. The original CrossWire archive and all six pinned CCEL originals remained unchanged. Public-domain **underlying historic text** is legally distinct from **CCEL electronic XML/markup and additions**.

Source-side web references useful for human comparison: [CCEL original Psalm 7](https://ccel.org/ccel/henry/mhc3/mhc3.Ps.viii.html), [CCEL original Acts 17](https://ccel.org/ccel/henry/mhc6/mhc6.Acts.xviii.html), [Bible Gateway Psalm 7:1–9 commentary](https://www.biblegateway.com/resources/matthew-henry/Ps.7.1-Ps.7.9), [Bible Gateway Acts 17:22–31 commentary](https://www.biblegateway.com/resources/matthew-henry/Acts.17.22-Acts.17.31). Their **independent textual lineage and exact paragraph equivalence have not been proven**. A separately digitized **printed volume III** witness is available from [Wikimedia Commons/Internet Archive](https://commons.wikimedia.org/wiki/File:A_commentary_on_the_Holy_Bible_-_with_practical_remarks_and_observations_(IA_commentaryonholy03henr).pdf); a printed volume VI must be independently verified before similar claims.

**Next editorial source gate:** privately compare each *exact extra `p`*, including whether it is verbatim Scripture, a source-edition annotation, or authored exposition, to the corresponding historic **printed** work and its chapter/section sequence. Record edition identity, pagination, strict passage ownership and reversible receipt. Do **not** use another website rendering alone as proof of print-edition independence. No source words/XML/SWORD binaries have been committed, no native keys reindexed, no package/catalogue/release emitted; draft PR #286 remains intentionally unmerged.

## Independent 1828 print-linked Psalm VII witness — editorial corroboration, not exact-byte approval

A separately provenance-described **1828 American printing / reprint** of Matthew Henry's *An Exposition of the Old and New Testament*, distinct from the six source-pinned CCEL ThML files and CrossWire MHC 2.2, is transcribed at [Wikisource's 1828 edition, Psalms VII](https://en.wikisource.org/wiki/An_Exposition_of_the_Old_and_New_Testament_%281828%29/Psalms). It links to the **scan-backed, validated source pages** [volume III page image #223 (printed page 215)](https://en.wikisource.org/wiki/Page:An_Exposition_of_the_Old_and_New_Testament_(1828)_vol_3.djvu/223) and [#224 (printed page 216)](https://en.wikisource.org/wiki/Page:An_Exposition_of_the_Old_and_New_Testament_(1828)_vol_3.djvu/224). Wikisource's [edition preface/provenance](https://en.wikisource.org/wiki/An_Exposition_of_the_Old_and_New_Testament_(1828)) describes the Towar & Hogan 1828 first American edition and the Barrington & Haswell reprint, **including a documented single-word plate correction in Psalm 7**. This witness must therefore not be silently treated as a byte-equivalent transcription of the CCEL electronic source.

**What these linked scan-transcription pages independently establish:** in the exposition on Psalm 7:1–9, between the numbered section **II** (David's plea of innocence) and numbered section **III** (David's appeal for divine judgment), the 1828-derived text explicitly **continues through the extended author's interpretation** of David's innocence and conscience, including the legal accusation, the episodes involving Saul's life, and the consequences of false appeals before God. The 1828-derived printing shows **the long intervening prose**, while the independently viewed general [Wikisource MHC Volume 3 / Psalms transcription](https://en.wikisource.org/wiki/Matthew_Henry%27s_Commentary_on_the_Whole_Bible/Volume_3/Psalms) **jumps straight from the brief Latin/English poetic quotation to section III**, likewise missing this intervening exposition. This is a highly localized comparison of *documented content continuity*, not evidence that Wikisource's general commentary transcription and CrossWire share a compiler or an upstream error.

**Result:** the source-only **569-word complete ThML paragraph at `Bible:Ps.7.1-Ps.7.9`** has a **historically printed editorial counterpart** supported by the scan-linked independently transcribed 1828 page sequence. The separately identified **16-word original ThML paragraph**, exact lexical identity, typographic boundaries, CCEL electronic markup and the attribution of every original word still require **direct page-image/manual collation** before a full authorial-fidelity gate can pass. A continuous printed exposition may have different paragraph formatting from CCEL. Do **not** reinsert CCEL electronic prose verbatim into CrossWire under this evidence alone; digital-edition rights remain uncleared.

**Acts 17:22–31:** the separate 235-word original CCEL paragraph still lacks a separately collated scan-backed printed witness. No editorial authorial-loss verdict, permission, native reindexing, public module, release or catalogue entry is implied. Preserve draft PR #286 and the source/stock raw SHA checkpoints.


## All six volumes: source-extra entire original paragraph SHA census (2026-11-17)

**Validated full-scope evidence:** [six independently pinned original source-to-stock volume jobs #44098512988](https://github.com/icfmp/Bible-Resources/actions/runs/44098512988), **6/6 SUCCESS** on original research script head `6ba81729bc9b081929cdc04842928eb309c7b6af`. Same revision independently passed [full Validate #44098512368](https://github.com/icfmp/Bible-Resources/actions/runs/44098512368), [tool registry #44098512340](https://github.com/icfmp/Bible-Resources/actions/runs/44098512340), full native original-corpus audit, source reference anchors and JSword. CCEL XML and original stock MHC bytes, K/I/TOP content and all source hashes remained unchanged. The 6 independently archived CI receipts are **metadata-only**, not republished original prose or XML.

The existing generic read-only comparator now authenticates every actual adjacent original CCEL ThML `p` element's ordered Unicode visible word-token count and SHA-256 and compares those **in private memory** with each exact extra *nonlinked* source word span after excluding only genuine CCEL `scripRef` and stock `reference` labels. This does **not** assume native section equivalence, source poem/heading authorship, or edit permission. It reconciles all **124** original source-extra unlinked-prose ordered cases:

| Original CCEL volume | Cases with at least one exact whole source `p` visible-word digest match | Ambiguous repeated word alignments | Unique gap with no exact whole source `p` digest match |
| --- | ---: | ---: | ---: |
| I (Genesis) | 0 | 0 | 1 |
| II | 0 | 0 | 0 |
| III (Psalms, Ecclesiastes) | **112** | **3** | 1 |
| IV (Isaiah, Jeremiah) | 0 | 1 | 3 |
| V | 0 | 0 | 0 |
| VI (Acts, Romans) | **1** | 0 | 2 |
| **Total** | **113** | **4** | **7** |

**Decisive positional pattern, Psalms:** of the **116** broad Psalms source-longer same-start cases, 112 have a **unique additional original entire paragraph** and **every one of those 112 original `p` matches is the very first `p` element (document ordinal 1) in its own original source `scripCom`-adjacent section body**; zero have another whole-`p` digest in this narrow primary classification. The three ambiguous Psalms cases are pinned to source Volume III XML **lines 28009, 46600 and 54125** with unchanged source full-reference/body SHA, but must remain unclassified. One remaining Psalms case instead has unlinked source/stock word selection or order divergence outside this 124-count ordered class. No absent source text is inferred from an unresolved case.

**Confirmed Psalm 7 title vs exposition distinction:** the unique 16-unlinked-word **first `p`** of original `Bible:Ps.7.1-Ps.7.9` is exactly the **KJV Psalm 7 superscription**, *not* lost Matthew Henry exposition. It has original `p` ordinal 1 and exact original visible Unicode word-token SHA `eeaf2603acdc86723cece6c14013311fe1da9b01c1a545cf3a7552fce6f6ae8c`. Its original extra **569 unlinked authorial-exposition words** are **different**, original `p` ordinal 6 (588 visible words including 19 genuine linked Bible-reference label tokens), original full `p` visible word-token SHA `0a733673d3b3cb71dee93dc4c454dfaddee08c9fc87d43d879c9e61ec402f68c`. The [1828 printed Psalm 7 witness](https://en.wikisource.org/wiki/Page:An_Exposition_of_the_Old_and_New_Testament_(1828)_vol_3.djvu/223) corroborates the *existence and placement* of this long exposition, but full scan transcription/word/punctuation collation and electronic-edition redistribution approval remain open. In the whole-`p` fingerprint census, only the 16-word first `p` is a whole **nonlinked** text match because the long `p` contains 19 real source-link label words. A failing 569-word full visible `p` digest match is **not** evidence it is only a partial original paragraph; the independent original `p` boundary audit already proved it is a whole paragraph.

**Acts 17:22–31:** a separate original **235-word entire `p`** at source document ordinal **17** is likewise a direct whole original `p` SHA match, with original visible word-token SHA `462ec448acf7e29788eeedfbb245ad08ea98faaade8c0dbef7755c042d2779cc`. Its historical print lineage remains to be verified directly; the separately sourced [1828 printed volume VI scan](https://commons.wikimedia.org/wiki/File:An_Exposition_of_the_Old_and_New_Testament_(1828)_vol_6.djvu) is available but the individual Acts 17 passage/pages have **not** yet been visually collated. A web transcription alone is not independent printed-edition proof.

**Next source-bound tests:** (a) independently identify which of the **111 additional** first-`p` Psalms observations are genuine canonical KJV superscriptions and which might be another source heading, by referencing a *separately pinned* authorized original KJV title witness rather than classifying by position alone; (b) examine original source lines 28009, 46600, 54125 and the remaining Psalms word-order case separately without guessing an anchor; (c) collate the exact original Psalm 7 long `p` and Acts 17 `p` against validated scanned print pages, document variant readings and issue-level editorial choices; and (d) obtain edition-specific redistribution/edit permission where needed. **No CCEL original text, original CrossWire compiled binary, module package, versification, source Scripture, public catalogue or release has been modified. Draft PR #286 stays unmerged.**
