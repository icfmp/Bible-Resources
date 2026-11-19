# MHCC Modern English — Proverbs 9–16 targeted fidelity follow-up

**2026-11-19 | PR #272 (draft), no approval to publish or merge.**

## Why this is a *targeted follow-up*, not a third complete translation pass

The established **translate → verify** editorial process is already complete for all **1,189/1,189** modern chapter manuscripts; this was explicitly documented in [the editorial protocol](../../../docs/MHCC_MODERN_ENGLISH.md). The earlier insistence on a third corpus-wide full rereading would duplicate that work. This follow-up instead checks already-identified **risk categories**: attenuated explicit theological vocabulary, divine agency, authorial assertions and translator/editor notes accidentally appearing as prose. No completed chapter-review status has been reset, and no extra general translation pass is being claimed.

## Evidence and scope

**Eight existing manuscripts**, Proverbs **9–16**, inspected side by side with the complete English chapter sections of CCEL's *Concise Commentary*. This is a **secondary digital English witness**, not an independent exact native source-semantic review. Source text from the released corrected `MHCC 0.1.1` remains authoritative for the derivative, and only exact K fingerprints/selected phrase presence can be tested automatically.

| Chapter | Targeted result |
| --- | --- |
| Proverbs 9 | No change needed in the selected categories; explicit *depths of hell* and both authorial divisions present |
| Proverbs 10 | No change needed in selected categories; preserve original chapter-level preface and verse-specific short expositions |
| Proverbs 11 | No change needed in selected categories; author's brief verse units retained |
| Proverbs 12 | No change needed in selected categories; no source-specific softening found |
| Proverbs 13 | No change needed in selected categories; source references including Matthew 12:37 remain distinct |
| Proverbs 14 | No change needed in selected categories; note that CCEL's original sequence moves from 12 to 14 without an independent verse-13 section (do not invent commentary) |
| Proverbs 15 | No change needed in selected categories; Christ's atonement and Spirit's gift of prayer remain present |
| Proverbs 16 | **Two localized changes to one draft manuscript**: source-specific judgment wording and improper translator annotation in the reader-facing prose |

### Proverbs 16:4 — restored specific source claim

- **Before:** generic `righteous judgment` and `final justice`.
- **After:** Henry's **righteous vengeance against the wicked** and **their destruction at last**.
- Witness: [CCEL Proverbs 16](https://ccel.org/ccel/henry/mhcc.xxi.xvi.html).
- This preserves the author's historical assertion; it does not newly formulate or endorse the claim as a doctrinal editorial decision.

### Proverbs 16:9–10 — move editorial explanation out of translation body

- The CCEL passage has an inline **“10.”** following the original prose for verse 9, with an exhortation that rulers and judges govern in the fear of God.
- The published original SWORD has a native numbered K entry at `Prov.16.9` but no independently occupied `Prov.16.10` K body; this is independently recorded in the successful full 1,189-chapter native receipt.
- The prior Modern English manuscript had mistakenly printed **“The CCEL paragraph then continues with an inline ‘10.’”** as part of the user-visible commentary. That is *translator metadata*, not Henry's content.
- The draft now gives only the exhortation, retains the original K-owned section, and moves the source-label explanation into the dated separate editorial review.
- Do not synthesize a source `Prov.16.10` K body, change a biblical verse reference, or edit the published original.

### Native source tests

The [existing private lexical source-probe manifest](PROVERBS_NATIVE_FIDELITY_SOURCE_ANCHORS_2026-11-19.json) has been extended to exact original `Prov.16.4` and `Prov.16.9` K identities, from successful full-canon source-native receipt logs, with two short source-claim anchors each. The existing original-source SHA-pinned `commentary_modern_native_witness_probe.py` and CI workflow validate **source phrase presence only**, not complete semantic equivalence or editorial acceptance. Do not mark native verification successful until the actual current-head GitHub Actions step has completed.

## Editorial disposition and boundaries

- **No global rereading of 1,189 manuscripts is required:** it has already been done under the approved two-stage method. Repeat only if a concrete defect, source ambiguity or publication-blocking discrepancy justifies it.
- Two localized, reversible changes were committed in **the draft modern text only**; prior translation/check results are retained.
- Original MHCC 0.1.1 binaries, native K/I ownership, source notes, original hyperlink targets, Bible app and catalog were not changed.
- The source digital edition and its relevant attribution remain separate from the modern draft's editorial annotations.
- The 11 quarantined original-link suspect occurrences, independent review requirements for actual problematic clauses, reader QA, rights clearance and explicit release approval remain separate issues; no independent full 1,189-chapter semantic sign-off or publication asserted.
