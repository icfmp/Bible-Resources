# MHCC Modern English — exact source-backed reference mapping checkpoint

**18 November 2026 — technical audit verified in CI; editorial review already performed during modernisation is reused, not restarted. Publication remains blocked.**

## Result

The complete **1,189-chapter** modern OSIS was rebuilt with a generic opt-in reference-matching pass in the existing `scripts/commentary_modern_reference_gate.py`. It reads the original `MHCC 0.1.1` **from the pinned original SWORD corpus**, authenticates **all 669 original link-bearing authored K groups** against the existing complete raw SHA/linked-element identity receipt, and only places a formerly unplaced source link if:

1. The real original link has an authenticated *single-verse* canonical destination and is neither covered by an existing reviewed placement nor by a documented proposed source-error correction.
2. Its original destination appears **exactly once as an explicit English “Book chapter:verse” citation inside the corresponding modern commentary section**, with no range, continuation or ambiguous repetition; nested already-linked text, original outline tables and headings are ignored.
3. Original links with ambiguous/incompatible syntax, multiple occurrences of the same target, suspicious one-digit visible source labels, or absent unique modern citations remain **untouched**.
4. The derived OSIS still contains the exact same modern visible prose and the **original literal osisRef** for automatically matched links. The existing, explicitly documented eight corrected targets remain isolated decisions, not assumed automatically.

There is **no fuzzy text placement, assumed source-link destination, invented verse text, change of original linked source material or blanket treatment of missing verses**. The result is a bounded technical source-to-modern concordance, **not automatic independent editorial approval**.

### Authentic whole-canon CI results

On the code head **`4366cdbbedcfd3a008522b1a8d16040a3b3ff2dc`**, all three workflows completed successfully:

- [Real original-source / modern OSIS / native compiled SWORD audit #44295690481](https://github.com/icfmp/Bible-Resources/actions/runs/44295690481) — **SUCCESS**.
- [Validate #44295690558](https://github.com/icfmp/Bible-Resources/actions/runs/44295690558) — **SUCCESS**.
- [Tool registry #44295690629](https://github.com/icfmp/Bible-Resources/actions/runs/44295690629) — **SUCCESS**.

| Verified derived artifact property | Result |
| --- | ---: |
| Previously reviewed modern OSIS inline links | **39** |
| **New authenticated exact single-verse source matches** | **497** |
| **Total derived modern OSIS inline links** | **536** |
| Authenticated original source link elements now represented | **535 / 1,204 (44.4%)** |
| Extra link authored in modern text but missing from original source XML | **1**, Rev.22.2 |
| Distinct original authored K bodies containing derived links | **406** |
| Original link-bearing K bodies authenticated for safe matching | **669 / 669** |
| Original + narrowly permitted I-only SWORD numbered verse addresses | **28,792 / 28,792**, no extras or missing |
| Actual native SWORD linked destination SHA-256, in derived order | **536 / 536 match** |
| Actual native SWORD visible link-label SHA-256, in derived order | **536 / 536 match** |
| Modern commentary visible prose modified by link overlay | **No** |
| Original published MHCC module modified | **No** |
| Independent full original-format / modern semantic publication approval | **No** |

The compiled whole-canon module is a disposable private technical candidate `MHCCLINKTMP`. The full derived OSIS SHA-256 in the CI metadata report is `973b7f13cebdf10ab4e4929bbba83496d416b16ce05d313471c4ee654a9e7fa1`; the file itself, the unpublished source corpus prose and the compiled derivative module **were not exported** from CI.

### Recorded, non-silent exclusions from this conservative pass

The source audit also reported counts for the remaining source hyperlink elements:

| Auto-pass disposition | Original link occurrences |
| --- | ---: |
| Reviewed source-linked placements already supplied manually | 38 |
| Authenticated source correction/omission proposals excluded from the auto-pass | 9 |
| **Original `osisRef` incompatible with the narrow single-verse recognizer** | **513** |
| No unique, explicit modern full English book/chapter/verse citation at the authenticated original source section | **134** |
| Original displayed source label empty or suspicious single digit | **13** |
| Original source target repeated within same authored group | **0** |

These categories **are not proof of errors in the original text**. In particular, the 513 unsupported `osisRef` values may be valid OSIS ranges or compound expressions: they need a separate, format-aware analysis before any further automatic transfer. The 134 nonmatches may include legitimate abbreviations and citations whose reader-friendly presentation differs from original markup. No reference was invented or silently removed to increase coverage.

The 1,204 original hyperlink elements break down as **535 represented in the derivative (including eight verified target corrections), 9 spurious original hyperlink elements deliberately excluded under existing documented source dispositions, and 660 other occurrences still to place or review** (513 + 134 + 13). There is also one added authorial citation that was never linked in the original module. Never classify unmatched source markup as automatically wrong or unimportant.

## Safe next actions

- Inspect the **shape and grammar** of the remaining original compound/ranged `osisRef` attributes via authenticated private source parsing and a metadata-only report; support exact matching of individually verified standard range forms in the existing generic processor, rather than hardcoding a list of difficult chapters.
- Evaluate remaining abbreviation/multiple-label cases without changing the already reviewed modern manuscript prose.
- Recompile to isolated SWORD, re-run whole-canon exact 28,792-key occupancy and source-linked target/visible-text integrity after every batch; retain draft PR #272 and issue #270, and do not publish or merge before the outstanding source structure, rights and owner-authorized release gates.

**Editorial scope:** The 1,189 manuscript translations already received the planned translation-followed-by-check review. That review is **not** restarted. The remaining quality checks focus on retaining already-reviewed content in transport and resolving genuine source/format ambiguities, not imposing a third mandatory global editorial rewrite.
