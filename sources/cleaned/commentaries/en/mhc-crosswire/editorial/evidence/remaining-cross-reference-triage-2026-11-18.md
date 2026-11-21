# MHC — 25 verified machine-reference corrections

**Final conclusion:** 25 malformed, ambiguous or noncanonical original `reference/@osisRef` destinations were individually reviewed and corrected **without changing any displayed Scripture label or commentary prose**. The approved corrections appear in [MHC 0.1.0](../releases/MHC-0.1.0.md) and its [source manifest](../../CLEANUP_MANIFEST.json).

## Why these changes were needed

Source citation labels and their machine-readable SWORD destinations are distinct. Examples in the original CrossWire OSIS included bare numeric `21.13` in an identified book context, inherited-book compound references and ambiguous title/superscription targets.

The generic parser cannot fix all such cases by "best guess": each proposed destination required the exact authorial source line, original visible label and independent Bible reference evidence. Machine-only edits remain reversible and source-SHA-bound. The complete vetted mapping is in the maintained source/rebuild ledger; the former 7→14→17→24→25 proposal chronology is available in Git history.

## Native and reader acceptance are different

- An independent private native SWORD rebuild verified the **25/25 corrected `osisRef` destinations** against their reviewed original source anchors. [Original technical proof #44303621820](https://github.com/icfmp/Bible-Resources/actions/runs/44303621820).
- That check did **not** prove every Xiphos/AndBible mouse-click route. Particularly, a printed **Psalm 60 superscription** link can be interpreted differently by readers even when its machine target is source-attested.
- Do not modify the authorial wording to disguise a client navigation problem or silently turn a verse title into verse text.

See [reader acceptance limits](reader-acceptance-scope-2026-11-19.md) and [released MHC module](../releases/MHC-0.1.0.md). Any new destination needs new source evidence; this list is **closed for the approved 0.1.0**, not a reusable heuristically generated cross-reference table.
