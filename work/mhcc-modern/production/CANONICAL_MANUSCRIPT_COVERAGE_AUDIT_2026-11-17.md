# MHCC Modern English — canonical manuscript coverage and release-gate audit

**Audit date:** 2026-11-17  
**Repository:** `icfmp/Bible-Resources`  
**Draft PR:** [#272](https://github.com/icfmp/Bible-Resources/pull/272)  
**Audited PR head:** `f8700680d2f0951277b2c28a25865d1109a3196a`  
**Canonical tracking issue:** [#270](https://github.com/icfmp/Bible-Resources/issues/270)  
**Verdict:** **CANONICAL MANUSCRIPT COVERAGE PASS; FULL ORIGINAL-NATIVE AND INDEPENDENT EDITORIAL ACCEPTANCE NOT TESTED. DO NOT MERGE OR PUBLISH.**

## What was actually verified

The audit enumerated **all 1,294 changed file paths** reported for PR #272, inspected the complete added text of the 1,189 chapter manuscripts, and checked the chapter list against GitHub issue #270. The remaining 105 changed files concern the production workflow, book-introduction candidates, pilots, evidence, tools and tests.

| Check | Result | Significance |
| --- | ---: | --- |
| Distinct canonical Modern English chapter files under `work/mhcc-modern/production/accepted/` | **1,189 / 1,189** | Every intended canonical chapter has a distinct manuscript. |
| Book-specific filename groups | **66 / 66** | One complete Protestant 66-book chapter inventory, including all 150 Psalms. |
| Gaps in chapter-number sequence within any book | **0** | No missing chapter-number filenames. |
| Duplicated `chapter_osis` identifiers | **0** | Every manuscript declares a unique OSIS chapter. |
| OSIS chapter-number suffix matching manuscript filename | **1,189 / 1,189** | No filename/OSIS chapter-number mismatch detected. |
| Pinned source release ZIP SHA and native corpus SHA | **1,189 / 1,189** | All manuscripts identify the same published `MHCC` 0.1.1 baseline. |
| Explicit `NOT RELEASED` publication metadata | **1,189 / 1,189** | No manuscript presents itself as a released SWORD module. |
| A review / audit / acceptance-record heading | **1,189 / 1,189** | Review notes exist; their existence does **not** establish their independence or truth. |
| Some explicit caveat about missing native, independent or SWORD verification | **1,189 / 1,189** | The outstanding release gate is acknowledged. |
| Separate introduction candidates | Present for many books | Candidate presence does not prove its original native SWORD location. |

**Methodological limit:** These checks establish the existence, indexing, consistency of declared source identities and recorded draft-review notes **in the PR changed text**. They do **not** compare the text against every original word, note, SWORD key, `osisRef`, paragraph or authorial heading. The directory name `accepted` and the manuscript status `CHAPTER-LEVEL REVIEW COMPLETE` are **not independent publication acceptance**.

### Nonuniform representations requiring careful treatment

- **54 manuscripts** do not cite a `ccel.org` URL in their review text. Many cite other English reading witnesses such as STEP, BibleStudyTools or an alternate historical transcription. This is **not automatically missing source material**, but their provenance and source equivalence must be verified before independent editorial approval.
- **21 manuscripts** do not use a conventional `## Original ...` section. Some authorial source comments have no distinct heading or outline; see Genesis 36 and the continuous Proverbs chapter comments. Do **not** invent missing source divisions to satisfy a superficial format check.
- Earlier chapters use several editorial status conventions, including `CHAPTER-LEVEL REVIEW COMPLETE`, while later ones explicitly say `ORIGINAL-NATIVE SWORD VALIDATION PENDING`. All files retain a caveat in the prose and/or metadata. Do **not** reinterpret earlier status text as full acceptance.
- Very short manuscripts are plausible when Henry's original authorial commentary itself is very short or is only a reference to a parallel passage. Examples: 1 Chronicles 14, Isaiah 36, Ezekiel 41. Verify the *source* before flagging them as omissions or expanding them.
- **Genesis 1** includes the book introduction in the accepted chapter manuscript as part of a source-specific analysis; a separate introduction candidate also exists. The exact native ownership/mapping must determine how to avoid duplication in the eventual structured edition.

### Source-specific cases to keep visible

1. **Genesis 5:** a broken phrase in a digital witness required an alternate historical witness. Track its documentary evidence and avoid unapproved edits to the original published `MHCC` edition ([issue #291](https://github.com/icfmp/Bible-Resources/issues/291)).
2. **Exodus 1:** the secondary [CCEL chapter outline](https://ccel.org/ccel/henry/mhcc.iii.i.html) places the text for Israel's increase beside **8–14** and the oppression heading beside **1–7**. The manuscript preserves this *as printed* while ordering the actual exposition sections chronologically. Treat it as a **secondary-witness editorial inconsistency**, not a reason for a silent correction to the pinned original.
3. **Amos:** some secondary witnesses have irregular CCEL URLs or require other corroborating English witnesses. Do not silently treat a missing normal CCEL URL as a missing chapter.
4. **Isaiah 36:** the original Henry commentary is an explicit cross-reference to **2 Kings 18:17–37**, not newly composed Isaiah prose. Preserve that reference and never materialize invented exposition.
5. **Ezekiel 41:** the short prose (two original witness sentences) is a real content shape, not evidence by itself of truncation.
6. **Revelation 22:** the printed source outline refers separately to **verses 20 and 21** in one authorial commentary group. Do not infer a single merged native SWORD verse key.

## Actual CI evidence at audited head

- **Validate:** success.
- **Modern commentary source-native receipt (metadata-only):** success. The present workflow inspects the released source and **Genesis 1** plus a 24-chapter pilot/draft evidence set. Its success is **not full 1,189-chapter native mapping or modern semantic acceptance**.
- **Tool registry consistency:** **failure**. Latest observed failing command: `python scripts/tool_registry.py --check`; the output reports `Tool inventory changed: docs/TOOL_REGISTRY.json, docs/TOOL_REGISTRY.md` ([run](https://github.com/icfmp/Bible-Resources/actions/runs/44176837760)). This is a real PR check failure and must not be labeled green or quietly ignored. Do not alter the repository's global registry by guessing; regenerate and independently inspect the deterministic output in a focused maintenance change.

## Remaining gates before an edition can be accepted

1. **Original-native provenance and exact structure:** verify the SHA-pinned 0.1.1 release and complete ordered **29,975** original native entries (28,742 numbered keys, 1,255 intro keys and two other top entries) with the established reader. Map all unique authorial commentary bodies, range/verse identity, book/chapter introductions, notes, cross-references, quotations and ordered markup to the 1,189 derivative manuscripts. Distinguish shared/ranged source entries from truly separate text. No invented source locations.
2. **Independent editorial and theological collation:** a reviewer other than the drafting pass must compare **every substantive statement and qualification** to the exact compiled original source, while recognizing CCEL/STEP/other transcriptions as secondary witnesses only. Record corrections with chapter and source evidence.
3. **Build and round-trip:** create a *new* derivative module from reviewed structured data, not these Markdown drafts, and audit complete key ordering, source reference targets, introductions, nonduplicated ranged bodies, Unicode and text fidelity after SWORD compilation/readback.
4. **Reader checks:** verify practical navigation, source links, poetry/paragraphs, intro placement and representative long passages in independent SWORD readers. Avoid treating a CLI, metadata check or headless UI process as proof of real GUI rendering.
5. **Rights and publication:** verify digital source and translation derivative rights; obtain explicit editorial, technical and owner publication authorization, decide the final separate module ID and catalogue metadata, and release only after passing every preceding gate.

## Tracking reconciliation

Issue #270 previously held **1,120 checked chapter rows and 69 unchecked rows**, even though all 69 manuscripts from 1 Timothy through Revelation were independently identified in the PR. Every previously unchecked entry was verified against the PR path inventory. Because the full issue body had grown to about **259 KB**, it was **archived verbatim** in [the historical snapshot](checkpoints/issue-270-body-2026-11-17-pre-reconciliation.md) and the live issue was **compacted** to an actionable release-gate checklist (with successful issue readback). The live issue now reports **1,189/1,189 manuscript files present**, *not* 1,189 independently accepted chapters; the archived historical checkbox state remains available for audit and has not been retroactively edited.

**Next actionable work:** resolve the actual registry check blocker in the proper scope, expand source-native receipts beyond the historical pilot, then independently collate the manuscripts against `MHCC` 0.1.1 in small, reviewable batches. Do not produce duplicate translations.
