# Historical 69 unchecked chapters — native structural translation-coverage audit

**Scope:** the precise **69** chapter rows still marked `[ ]` in the [immutable issue #270 historical snapshot](checkpoints/issue-270-body-2026-11-17-pre-reconciliation.md). The old checklist status was not treated as either evidence of absence or proof of completion.

**Published authoritative source:** corrected SWORD `MHCC` **0.1.1**. SHA-256 of immutable released ZIP: `a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746`. SHA-256 of ordered native corpus: `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`.

## Direct audit result — 2026-11-17

- **69 / 69 actual unshipped Modern English chapter manuscripts found and read**, from 1 Timothy 1 to Revelation 22 (12 books).
- **225 distinct numbered K source commentary units versus 225 distinct modern exposition sections**, in source order. All 69 had matching occupied native verse-unit bounds in the first diagnostic, beyond mere file existence.
- **1,380** occupied source K verse addresses across these chapters.
- **41,191** words in the modern exposition sections themselves (excluding frontmatter, original printed-outline table and editorial audit notes). No empty or placeholder sections were detected in the manuscript scan.
- All manuscripts keep their declared publication status `NOT RELEASED` and the original SHA identities. The first automation run [#44191493080](https://github.com/icfmp/Bible-Resources/actions/runs/44191493080) did **not** go green: an overly restrictive audit-script metadata-key parser excluded digits in `source_zip_sha256`, generating **69 false source-pin errors**. It was fixed in [commit `388d5d8`](https://github.com/icfmp/Bible-Resources/commit/388d5d8a5c21de038c648b48edd668ca68f5e79b), without altering any chapter translation. The corrected, restored workflow [**Actions #44192642018**](https://github.com/icfmp/Bible-Resources/actions/runs/44192642018) is now **SUCCESS**: the independent source-native 69-chapter step reports **69 manuscripts / 69 historical rows, 225 original K units / 225 modern sections, 1,380 occupied original K keys, 41,191 modern exposition words, ZERO structural problems**, with all 34 synthetic tests also passing. The earlier false source-pin report was strictly a checker parsing defect; the 69 manuscripts themselves did not require modification.

The structural source receipt is generated using real published libSWORD native K/I records and a complete-corpus SHA match, not inferred from published outlines or CCEL alone. The separate *source prose* itself and raw SWORD XML are never uploaded to GitHub Actions artifacts.

## Each of the 69 historical unchecked chapters

| Historic issue label | Original native commentary units | Modern prose sections | Occupied original K verse keys | Modern exposition words | Manuscript |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 Timothy 1 | 4 | 4 | 20 | 449 | [source candidate](accepted/first-timothy-01.md) |
| 1 Timothy 2 | 2 | 2 | 15 | 481 | [source candidate](accepted/first-timothy-02.md) |
| 1 Timothy 3 | 3 | 3 | 16 | 454 | [source candidate](accepted/first-timothy-03.md) |
| 1 Timothy 4 | 3 | 3 | 16 | 398 | [source candidate](accepted/first-timothy-04.md) |
| 1 Timothy 5 | 4 | 4 | 25 | 498 | [source candidate](accepted/first-timothy-05.md) |
| 1 Timothy 6 | 4 | 4 | 21 | 771 | [source candidate](accepted/first-timothy-06.md) |
| 2 Timothy 1 | 3 | 3 | 18 | 488 | [source candidate](accepted/second-timothy-01.md) |
| 2 Timothy 2 | 4 | 4 | 26 | 534 | [source candidate](accepted/second-timothy-02.md) |
| 2 Timothy 3 | 3 | 3 | 17 | 493 | [source candidate](accepted/second-timothy-03.md) |
| 2 Timothy 4 | 5 | 5 | 22 | 445 | [source candidate](accepted/second-timothy-04.md) |
| Titus 1 | 3 | 3 | 16 | 382 | [source candidate](accepted/titus-01.md) |
| Titus 2 | 3 | 3 | 15 | 493 | [source candidate](accepted/titus-02.md) |
| Titus 3 | 3 | 3 | 15 | 541 | [source candidate](accepted/titus-03.md) |
| Hebrews 1 | 2 | 2 | 14 | 489 | [source candidate](accepted/hebrews-01.md) |
| Hebrews 2 | 4 | 4 | 18 | 577 | [source candidate](accepted/hebrews-02.md) |
| Hebrews 3 | 3 | 3 | 19 | 481 | [source candidate](accepted/hebrews-03.md) |
| Hebrews 4 | 2 | 2 | 16 | 500 | [source candidate](accepted/hebrews-04.md) |
| Hebrews 5 | 2 | 2 | 14 | 321 | [source candidate](accepted/hebrews-05.md) |
| Hebrews 6 | 3 | 3 | 20 | 522 | [source candidate](accepted/hebrews-06.md) |
| Hebrews 7 | 4 | 4 | 28 | 475 | [source candidate](accepted/hebrews-07.md) |
| Hebrews 8 | 2 | 2 | 13 | 366 | [source candidate](accepted/hebrews-08.md) |
| Hebrews 9 | 5 | 5 | 28 | 655 | [source candidate](accepted/hebrews-09.md) |
| Hebrews 10 | 5 | 5 | 39 | 660 | [source candidate](accepted/hebrews-10.md) |
| Hebrews 11 | 6 | 6 | 40 | 1161 | [source candidate](accepted/hebrews-11.md) |
| Hebrews 12 | 3 | 3 | 29 | 621 | [source candidate](accepted/hebrews-12.md) |
| Hebrews 13 | 4 | 4 | 25 | 662 | [source candidate](accepted/hebrews-13.md) |
| James 1 | 5 | 5 | 27 | 836 | [source candidate](accepted/james-01.md) |
| James 2 | 2 | 2 | 26 | 558 | [source candidate](accepted/james-02.md) |
| James 3 | 2 | 2 | 18 | 351 | [source candidate](accepted/james-03.md) |
| James 4 | 2 | 2 | 17 | 533 | [source candidate](accepted/james-04.md) |
| James 5 | 4 | 4 | 20 | 714 | [source candidate](accepted/james-05.md) |
| 1 Peter 1 | 4 | 4 | 25 | 745 | [source candidate](accepted/first-peter-01.md) |
| 1 Peter 2 | 4 | 4 | 25 | 614 | [source candidate](accepted/first-peter-02.md) |
| 1 Peter 3 | 3 | 3 | 22 | 629 | [source candidate](accepted/first-peter-03.md) |
| 1 Peter 4 | 3 | 3 | 19 | 548 | [source candidate](accepted/first-peter-04.md) |
| 1 Peter 5 | 3 | 3 | 14 | 491 | [source candidate](accepted/first-peter-05.md) |
| 2 Peter 1 | 3 | 3 | 21 | 664 | [source candidate](accepted/second-peter-01.md) |
| 2 Peter 2 | 3 | 3 | 22 | 548 | [source candidate](accepted/second-peter-02.md) |
| 2 Peter 3 | 3 | 3 | 18 | 599 | [source candidate](accepted/second-peter-03.md) |
| 1 John 1 | 2 | 2 | 10 | 444 | [source candidate](accepted/first-john-01.md) |
| 1 John 2 | 6 | 6 | 29 | 858 | [source candidate](accepted/first-john-02.md) |
| 1 John 3 | 5 | 5 | 24 | 760 | [source candidate](accepted/first-john-03.md) |
| 1 John 4 | 3 | 3 | 21 | 676 | [source candidate](accepted/first-john-04.md) |
| 1 John 5 | 5 | 5 | 21 | 1073 | [source candidate](accepted/first-john-05.md) |
| 2 John 1 | 4 | 4 | 13 | 512 | [source candidate](accepted/second-john-01.md) |
| 3 John 1 | 3 | 3 | 14 | 524 | [source candidate](accepted/third-john-01.md) |
| Jude 1 | 5 | 5 | 25 | 1184 | [source candidate](accepted/jude-01.md) |
| Revelation 1 | 4 | 4 | 20 | 879 | [source candidate](accepted/revelation-01.md) |
| Revelation 2 | 4 | 4 | 29 | 745 | [source candidate](accepted/revelation-02.md) |
| Revelation 3 | 3 | 3 | 22 | 954 | [source candidate](accepted/revelation-03.md) |
| Revelation 4 | 2 | 2 | 11 | 392 | [source candidate](accepted/revelation-04.md) |
| Revelation 5 | 2 | 2 | 14 | 546 | [source candidate](accepted/revelation-05.md) |
| Revelation 6 | 3 | 3 | 17 | 758 | [source candidate](accepted/revelation-06.md) |
| Revelation 7 | 3 | 3 | 17 | 514 | [source candidate](accepted/revelation-07.md) |
| Revelation 8 | 2 | 2 | 13 | 509 | [source candidate](accepted/revelation-08.md) |
| Revelation 9 | 2 | 2 | 21 | 405 | [source candidate](accepted/revelation-09.md) |
| Revelation 10 | 2 | 2 | 11 | 338 | [source candidate](accepted/revelation-10.md) |
| Revelation 11 | 3 | 3 | 19 | 678 | [source candidate](accepted/revelation-11.md) |
| Revelation 12 | 3 | 3 | 17 | 683 | [source candidate](accepted/revelation-12.md) |
| Revelation 13 | 2 | 2 | 18 | 559 | [source candidate](accepted/revelation-13.md) |
| Revelation 14 | 3 | 3 | 20 | 556 | [source candidate](accepted/revelation-14.md) |
| Revelation 15 | 2 | 2 | 8 | 394 | [source candidate](accepted/revelation-15.md) |
| Revelation 16 | 4 | 4 | 21 | 580 | [source candidate](accepted/revelation-16.md) |
| Revelation 17 | 3 | 3 | 18 | 603 | [source candidate](accepted/revelation-17.md) |
| Revelation 18 | 3 | 3 | 24 | 527 | [source candidate](accepted/revelation-18.md) |
| Revelation 19 | 2 | 2 | 21 | 530 | [source candidate](accepted/revelation-19.md) |
| Revelation 20 | 4 | 4 | 15 | 684 | [source candidate](accepted/revelation-20.md) |
| Revelation 21 | 3 | 3 | 27 | 808 | [source candidate](accepted/revelation-21.md) |
| Revelation 22 | 3 | 3 | 21 | 771 | [source candidate](accepted/revelation-22.md) |

## What this DOES NOT prove

**The 69 historical unchecked rows concern real produced translations, not 69 missing chapters.** This report establishes substantive prose **coverage and source structural alignment only**. It does **not** independently prove that every original English sentence, theological qualification, example, reference, footnote, book introduction, paragraph or textual nuance has been faithfully carried over. A translation can contain an aligned section yet still omit or distort part of its meaning.

Every one of these 69 chapters must still receive an **independent original-native semantic review**, especially its references, source notes and any book introduction with substantive source text, followed by separately documented SWORD derivative compilation/readback, external reader acceptance, rights and owner publication authorization. A checked GitHub box is never a substitute for this evidence.

**No original MHCC 0.1.1 source, versification, published module, release, or semantic approval has been changed.** Draft PR #272 remains a draft.
