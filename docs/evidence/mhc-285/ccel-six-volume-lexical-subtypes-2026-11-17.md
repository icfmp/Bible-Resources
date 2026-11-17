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

## Further gates

The previous SHA-pinned full six-volume census already accounted for all **4,263** original verse/range section markers and **1,306** separate chapter markers (5,569 total `scripCom`). The subsequent detailed lexical comparison is **a classification of the 1,606**, **not** a claim that the other 2,648 whitespace-only cases or the 5 nonvisible source divisions have complete markup/section/edition parity. The four unoccupied original source starts remain under the previously classified CCEL index / source-grounded alias issues #288 and #290.

The bounded separate nonlink-word alignment remains incomplete for **20** source order/selection cases plus **46** original sections exceeding the LCS resource budget. Those should be independently reviewed using explicit exact-source/stock provenance, with any efficient order-only check labelled **not a full word-order difference magnitude or textual identity result**. Inspect cases in volume III first for source/compiled edition differences, then volumes V and VI for oversize alignments.

**No authorial source XML, original CrossWire binary, original scriptural reference, published commentary module or catalogue entry was modified.** The PR remains **draft**. Real corrected-candidate Xiphos/AndBible GUI acceptance, complete source/stock authorial word+punctuation+markup+division parity, copyright permissions and editorial approval remain **OPEN**.
