# MHCC Modern English — Job 1–8 focused English-source fidelity review

**2026-11-19 — draft PR #272; not publication approval.**

## Method

Read the complete chapter texts of [CCEL's Matthew Henry *Concise Commentary*, Job 1–8](https://ccel.org/ccel/henry/mhcc.xix.html) and compared them against the existing chapter drafts, original authorial section boundaries, explicit divine agency, judgment and Christological statements. This is a **separate online English witness**, not a complete independently authenticated edition-level native MHCC 0.1.1 semantic review. Original module/source, metadata, K ranges, and source reference destinations remain untouched.

| Chapter | Review outcome |
| --- | --- |
| Job 1 | No further substantive draft change in this focused pass. |
| Job 2 | No further substantive draft change; ambiguous/defective source concluding phrase still needs source-native comparison. |
| Job 3 | No further substantive draft change; source digital typo noted in existing manuscript. |
| Job 4 | **Draft corrected**: restore Henry's explicit contrast *wonder that one is not already in hell*; former text was generic deferred divine judgment. |
| Job 5 | **Draft corrected**: retain Henry's claim that afflictions **are from God**, rather than merely under divine governance; human sin remains distinct. |
| Job 6 | **Draft corrected**: preserve the active form of God *laying a burden upon us*, rather than merely permitting pain. |
| Job 7 | No further substantive draft change. |
| Job 8 | No further substantive draft change. |

These are **three** documented and reversible proposed fidelity amendments; their own chapter review notes and Git history contain before/after and provenance. Published original SWORD was never rewritten. They are not independent theological approval.

## Exact released source K-gate

The existing `commentary_modern_native_witness_probe.py` and complete native source-receipt workflow have been reused, not replaced with a Job-only importer. Additional SHA-pinned original `MHCC 0.1.1` K groups and short secondary-witness lexical anchor sets were recorded for **Job 4:12–21, 5:6–16, 6:1–7** in [the reversible probe manifest](JOB_NATIVE_FIDELITY_SOURCE_ANCHORS_2026-11-19.json). This manifest also covers earlier Job 21/24–42 restorations. Each K identity was copied from an actual successful 1,189-chapter source-native receipt, not inferred from modern headings.

Workflow result must be read on the **commit that includes the manifest and guard**, never from earlier green runs; a matched lexical anchor is evidence of a source clause's presence, **not** full semantic, punctuation, note, reference or reader parity. Any absent anchors must be treated as **witness disagreement requiring investigation**, not silently rewritten source text.

## Remaining gates

1. Resolve all native anchor results and any source/CCEL word differences.
2. Complete independent original-native semantic collation, including the remaining Job manuscripts not in this focused review.
3. Maintain full modern OSIS→SWORD readback and actual Xiphos/AndBible UI acceptance as distinct gates.
4. Verify derivative rights and obtain separate owner authorization before distribution.

Original source and Bible app untouched; PR remains **draft, unmerged, unreleased**; no additional `0/1,189` independent chapter signoffs are claimed.
