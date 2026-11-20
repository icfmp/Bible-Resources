# MHCC Modern English — authenticated chapter-outline references restored in private OSIS/SWORD

**2026-11-18 checkpoint.** Real source-native and full-canon private SWORD pipeline **PASS**; not an edited/published module. The modern manuscripts already underwent the agreed translation → editorial-check cycle; this operation does not restart that review or modify their wording.

## Complete OSIS/SWORD evidence

- Authentic **MHCC 0.1.1** original SWORD zip and raw-K corpus remain SHA pinned (whole original raw SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`), **unchanged**.
- All **1,189 chapters** modern English compiled in one private OSIS and disposable `MHCCLINKTMP`. Original **28,742 K** addresses, plus **50** narrowly scoped I-only transport aliases: **28,792 / 28,792 exact native SWORD numbered addresses**. Source K grouping remains unchanged.
- The prior **566** modern OSIS links comprised **38** mapped original manuscript-reviewed hyperlinks, **527** source-SHA-authenticated explicit full-book citation matches (including **30** explicit same-chapter ranges), and **one** independently documented authorial `Rev.22.2` witness missing from original source link markup. The eight original wrong targets are counted within the 38 mapped original reviewed links.
- **448 additional source-native chapter-outline hyperlinks** were restored in **180 modern chapter-I outline tables**. Strict acceptance requires the original source link to belong to the *original first K authored body*, its original (source-verified) literal full OSIS range to be in that same chapter, its visible original link label to explicitly identify the identical chapter and range, and exactly **one** corresponding original-outline table verse cell in the modern manuscript. The original literal target is preserved, with **no text edit** to the modern chapter outline or exposition.
- Each restored outline link is **explicitly relocated** from the original first-K source-owned chapter navigation into the corresponding modern **chapter-I** original-outline table. This preserves the **navigational destination and existing modern outline text**, but changes the exact native storage location by design. **Reader UI behavior must be tested before editorial release**: real native I readback proves metadata transport, not that every SWORD reader renders I introductions.
- Modern OSIS now contains **1,014** exact verified `<reference>` elements, representing **1,013 / 1,204 original source link occurrences (84.1%)** plus the separate one authorial missing-original-link witness.
- The compiled private real SWORD readback verified **all 1,014 / 1,014 literal target SHA-256 values, all 1,014 / 1,014 modern visible linked-label SHA-256 values and per-K/per-I document ordering**. **566** are in modern K body references across **428 K units**, **448** in chapter-I outline tables across **180 I groups**.
- The existing full-text integrity gate also passes: **4,038 / 4,049** authored modern K bodies are **exact visible Unicode matches** after SWORD compilation; the remaining **11** contain the entire expected text contiguously inside a surrounding wrapper, with **zero nonmatching or unparseable units**. This tests modern OSIS→SWORD transport, not an independent rereading of Henry's English.

The linked OSIS produced at this checkpoint had SHA-256 `3b0fc4e6dd2397a5093d12c439a1878108bd35f16e7767a620a0e467d3d669fb`. The full original prose, linked modern OSIS, and compiled zCom binary are **not publicly exported** by CI. Metadata-only artifacts hold hashes, counts, source key IDs and explicit NOT-PUBLISHED flags.

### Exact successful GitHub Actions

- [Authentic source + complete linked OSIS + native compiled K/I readback #44305087080](https://github.com/icfmp/Bible-Resources/actions/runs/44305087080): **SUCCESS**.
- [Validate #44305086669](https://github.com/icfmp/Bible-Resources/actions/runs/44305086669): **SUCCESS**.
- [Tool registry consistency #44305086756](https://github.com/icfmp/Bible-Resources/actions/runs/44305086756): **SUCCESS**.

## Remaining source hyperlink dispositions

| Category | Original link occurrences |
| --- | ---: |
| Authenticated original source links now represented in derived OSIS | **1,013** |
| Already witnessed and reviewed spurious original numeric-list hyperlinks, deliberately omitted | **9** |
| Remaining original links without one unique full-book singleton citation in the correct modern K prose | **134** |
| Original range links still without a unique match in prose or chapter-outline table | **32** |
| Original target syntax not accepted by the strictly bounded matcher | **3** |
| Original displayed single-digit link labels quarantined pending review | **13** |
| **Total original source elements** | **1,204** |

The **182 unresolved original links** are *not* 182 known data errors; many are legitimately abbreviated citations or original editorial quirks. Never auto-create missing verse text, link guessed scripture, or discard authorial notes to meet a numerical target. All **nine** spurious source hyperlink exclusions are separately attested; no original source binary is modified.

## Next independent steps

1. Triage the **182 unresolved source occurrences** in bounded batches using source SHA identities, retained translation-check manuscripts, reader-friendly context and the existing 17-case error disposition ledger. Prefer strengthening the generic parser where source syntax is unambiguous to hard-coded exceptions. Recompile SWORD and verify both K/I target and label hashes after every batch.
2. Verify on actual readers (**Xiphos and AndBible**), particularly original chapter-I outline visibility and the special I-only commentary cases (**Leviticus 19 and Psalm 108**).
3. Resolve the remaining quarantined **51 book-introduction candidates** only with real original native ownership evidence and no duplicate exposition; then perform release-level structure/rights checks and request explicit authorization before publication.

**State:** PR #272 remains **draft**; issue #270 remains **open**; no release, no merge, and no implied source-native editorial/publication signoff.
