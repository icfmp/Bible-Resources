# Modern English MHCC — canonical draft-outline range screen (2026-11-17)

**Status: 9 draft outline inconsistencies identified and 14 range cells
explicitly corrected in unreleased manuscripts.** No original source module,
commentary section boundaries, source-authored wording, paragraph text, or
book/chapter versification has been modified.

## Source and scope

- Authoritative original is the pinned published `MHCC 0.1.1` (ZIP
  `a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746`).
- CI heuristic screened all **1,189** current chapter Markdown manuscripts and
  evaluated **1,028** outline tables with numeric range rows. It could not
  evaluate **161** through this narrow table-row heuristic; this is **not** a
  complete source-to-draft outline audit.
- [Diagnostic CI #44188059428](https://github.com/icfmp/Bible-Resources/actions/runs/44188059428)
  reported **9** anomalies. Some previously copied original-outline range
  labels are impossibly descending; others are transposed relative to
  Scripture and the correctly aligned exposition section headings in the
  *same* modern manuscripts.
- The following recorded repairs are explicitly in the **modern derivative
  outline tables only**. Whether the underlying error originated in a
  particular original witness or in draft transcription is not asserted
  without an independent native I/K outline comparison.

## Exact changed references, with original manuscript labels preserved here

| Chapter | Original manuscript outline range(s) | Corrected modern outline range(s) | Explanation |
| --- | --- | --- | --- |
| Deut. 23 | cleanliness 15–25; servant/usury 9–14 | cleanliness **9–14**; servant/usury **15–25** | Two ranges transposed |
| Deut. 32 | Israel's wickedness 19–25; judgments 15–18 | wickedness **15–18**; judgments **19–25** | Two ranges transposed |
| Eccl. 5 | vanity of riches **9–7** | **9–17** | Invalid descending range; modern exposition spans 9–17 |
| Ezek. 3 | watchman **12–2** | **12–21** | Truncated end verse; next section begins 22 |
| Gen. 37 | Joseph sold **23–10** | **23–30** | Invalid end; next section begins 31 |
| Josh. 7 | God's instruction **10–5** | **10–15** | Invalid end; next section begins 16 |
| Luke 17 | forgiveness/humility 11–19; ten lepers 1–10 | first **1–10**; second **11–19** | Two ranges transposed |
| Num. 31 | culpability **13–38**; purification **39–24** | **13–18**; **19–24** | Both ranges repaired to the already aligned sections |
| 2 Sam. 2 | Asahel slain 25–32; withdrawal 18–24 | Asahel **18–24**; withdrawal **25–32** | Two ranges transposed |

Each manuscript's editorial review now records the old and new table-cell
values verbatim and the reason for the correction. There is no automated
prose rewrite, no change to source-authored topical headings or order, and no
invented verse-level commentary.

**Separate earlier flagged issue:** Exodus 1 contained a transposition of
the first two outline-row spans (8–14 vs. 1–7). The draft's explicit
correction was committed as
[`63abde3`](https://github.com/icfmp/Bible-Resources/commit/63abde3e0cf944d4f68d650c7c5dfafb7e0bbe1f)
before the 9-flag screen; the underlying CCEL witness was documented
separately.

## Verification and remaining gates

- Re-run the exact CI screen after these changes. Expected **zero flags
  under the same heuristic**, but do **not** claim this until a fresh Actions
  run confirms it.
- Independently compare original native `MHCC 0.1.1` I/K titles, tables,
  exact ranges, linked references and textual assertions for every affected
  chapter. Keep historical source errors visible in the audit; never modify
  the published `MHCC 0.1.1` without a separate approval.
- The 161 chapters not scanned by numeric table-row heuristics require
  source-aware inspection. Zero machine flags will **not** mean editorial
  approval for the 1,189-chapter modern edition.

The PR remains draft; no merge, release, or rights conclusion is authorized.
