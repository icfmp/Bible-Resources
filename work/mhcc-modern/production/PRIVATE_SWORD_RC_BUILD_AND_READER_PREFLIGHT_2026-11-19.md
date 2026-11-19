# MHCC Modern English — private SWORD release-candidate build and reader preflight

**2026-11-19 · PR #272 · PRIVATE / NOT APPROVED / NOT PUBLISHED**

This is the next **release-preparation** checkpoint after the completed *translate → verify* cycle for all 1,189 chapters and the targeted cleanup. It is **not a new translation pass**, a declaration of independent native-text semantic signoff, or authorization to merge/publish.

## Scope, immutable original, and candidate identity

| Item | Evidence / technical disposition |
| --- | --- |
| Authoritative original | Corrected SWORD **MHCC 0.1.1**, [published original release](https://github.com/icfmp/Bible-Resources/releases/tag/mhcc-0.1.1) |
| Original release ZIP SHA-256 | `a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746` |
| Original native corpus SHA-256 | `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e` |
| **Owner-selected complete display name** | **Henry's Modern Concise Commentary** (chosen 2026-11-19) |
| **Owner-selected short display name** | **HMCC Modern** (chosen 2026-11-19) |
| Temporary and isolated native SWORD ID | `MHCCMODRC` (kept for CI testing; not yet the approved public SWORD ID) |
| Candidate version / licensing metadata | `0.0.0` / `DistributionLicense=Private`; **not a redistribution-rights determination** |
| Native structure | **1,189 chapters / 4,049 K and I-only authored groups / 28,792 indexed verse keys** |
| Book introductions | **56 original-source-attested introductions** retained, with actual SWORD chapter-I transport proved earlier |
| Output | A **7-member compressed zCom SWORD installation-format ZIP**, compiled deterministically on the ephemeral GitHub Actions runner; **never uploaded as an artifact, release, catalogue asset or downloadable binary** |
| Preserved editorial source | All **1,189 existing modern manuscript files are unmodified**; no edits to published source, verse numbers or Bible application |

Full fail-closed machine-readable preflight configuration: [`PRIVATE_MODERN_RELEASE_CANDIDATE_PREFLIGHT_2026-11-19.json`](PRIVATE_MODERN_RELEASE_CANDIDATE_PREFLIGHT_2026-11-19.json). Reuse the established [native source receipt workflow](../../../.github/workflows/commentary-modern-source-receipt.yml); **do not** introduce a competing publication workflow or a new release plan before explicit approvals.

## Candidate text: documented, reversible conservative selection

The base is the privately tested complete modern OSIS/SWORD with authenticated original source links and 56 book introductions.

**Two complete, independently identified CCEL-only leaves are excluded in this *separate* source-strict candidate, not deleted from the modern manuscripts:**

1. `1Sam.25.39–44`, the separate CCEL exposition of David's marriage to Abigail; the authentic compiled original K `1Sam.25.32–44` instead contains the preceding 32–39 original exposition.
2. `Ps.95.7–11`, the separate CCEL warning; the authentic compiled original K `Ps.95.1–11` instead contains the preceding 1–7 original exposition.

The [two-case original K SHA-pinned source-strict manifest](PRIMARY_SOURCE_STRICT_TWO_SECTION_QUARANTINE_2026-11-19.json) records exact source identity, unchanged source-K ownership, and secondary-witness provenance. The complete original outlined verse spans are retained in chapter metadata as received; no K body, verse overlap or Bible passage is invented.

**Eleven separately attested digital or original-printed hyperlink defects remain *non-navigable* in the candidate only.** Exact source K/ordinal, original literal target SHA-256, original printed-label SHA-256 and original original-body SHA-256 are verified by the [eleven-case source errata manifest](ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json) and complete source-native ledger. The candidate removes only the navigation behavior: the derived source-note *visible labels remain verbatim unchanged*, visibly marked in its XML as `x-original-link-target-quarantined`. **No incorrect target is silently changed into a guessed replacement.**

- The **4 earlier malformed/wrong original hyperlinks** remain excluded; their separate **13 proposed** destinations are **not** in the candidate.
- The **11 additional defective source hyperlinks** have **15 separate witness-backed proposed** destinations in a distinct review-only preview; **none** are inserted in the conservative candidate.
- The **9 source-witness-confirmed spurious digital enumerator links** remain excluded.
- The previously restored valid original citation navigation is preserved as documented; the relocation of some source hyperlinks into modern outlines or introductions remains an **editorial transport**, not an unsupported claim that the original hyperlink was in the identical sentence.

Crucially, Jude's original `Jud` label is an ambiguous section-transition reference, and Numbers 29:1 carries an **original printed citation problem** (not merely broken digital navigation). Both remain explicitly quarantined pending approval.

## Automated technical release-candidate gates

The existing private full-canon GitHub Actions workflow now builds **`MHCCMODRC`** with `osis2mod -z z -b 3`, checks the actual seven-member native compressed package, builds a deterministic local ZIP, calculates SHA-256 and byte count of the package and each member, and writes **metadata-only** proof (not copyrighted authorial prose or a distributable module).

The candidate is read back through the real SWORD native reader and **compared with the complete source-strict compiled baseline**:

- All **4,049 / 4,049 authored original-group K bodies** are still present, with **exact visible text SHA equality** for each one.
- All **28,792 / 28,792** numbered addresses remain occupied as expected; no source-K alias or original verse key changes.
- The compiled original-links list for *every* K body equals the source-strict baseline **after and only after removing exactly the 11 known bad navigations**. All other in-prose links, editorial source-only supplement links and their labels retain exact identity and order.
- Existing chapter-I introduction text is exactly equal between compiled baseline and compiled candidate. No duplicate introduction or source comment body is produced.
- Seven actual **`diatheke`** readbacks test representative places: Genesis 1:1, Matthew 3:7, Leviticus 19:1, Psalm 95:1, 1 Samuel 25:32, Psalm 108:1, Revelation 22:2.
- Five negative provenance/approval tests fail closed if the original K SHA, original target, original printed label, approval status, or complete eleven-case manifest is tampered with.
- No release upload, Pages catalogue edit, PR merge or user-side installation occurs.

The metadata-only audit artifact retains `mhcc-modern-private-rc-metadata-only.json` (full package and seven member SHA-256 receipts), `mhcc-modern-private-release-candidate-preflight.json`, and `mhcc-modern-strict-primary-only-receipt.json`. The **actual package and OSIS prose remain private to the disposable runner**. Any eventual authorized public package will need a new exact-byte release approval and a real release plan.

## Remaining human/editorial and GUI acceptance — NOT automated away

| Release gate | What is required |
| --- | --- |
| Target corrections | Explicit accept/reject on each **11 + 4** source-erratum candidate, distinguishing original printed errors and section navigation; no blanket automatic replacement |
| CCEL-only sections | An editorial source/edition and separate **republication-rights** decision on the 1 Samuel 25 and Psalm 95 additions; the current conservative candidate deliberately excludes them |
| Editorial signoff | A human/independent acceptance record of remaining unverified **native semantics, source notes/paragraphs, formatting and original citation placement**; do not conflate the completed two-pass manuscript translation with this separate gate |
| Xiphos GUI | Actual installed build: verify modern text, note/heading visibility, 56 book introductions, 11 inactive suspect references, scroll behavior, I-only Leviticus 19 and Psalm 108, section overlap in 1 Samuel 25/Psalm 95 and Proverbs 16 label behavior; capture screenshots/versions/outcomes |
| AndBible GUI | Same representative verse navigation and notes, chapter-only sections, prefaces, cross-reference link activation/disabled status, and original-K verse coverage; record device/version and results |
| Rights and package | CrossWire original and CCEL textual scope, independent modification/redistribution permissions and metadata; select final **distinct** SWORD ID, version, module title/description/license, stable curated ID, packaging hashes, release notes and authorized release plan |
| Publication | Owner explicitly authorizes release after passing gates; only the existing release-before-Pages workflow may publish |

**We must not infer Xiphos or AndBible GUI success from diatheke/libSWORD CLI success. We must not mark any of these rows approved without direct evidence.**

## Evidence and status

The first complete private `MHCCMODRC` build and real reader compare **passed as an individual GitHub Actions step** on the current draft pipeline. The repository's read-only tool registry needed a subsequent metadata regeneration; the final status must be taken from the **latest PR-head** CI checks, not that intermediate run. Keep the PR draft pending all release-specific permissions.

The candidate-building workflow is intentionally part of the existing reproducible test infrastructure, **not a new publication path**. No new commentary resource has been advertised as available for download.
