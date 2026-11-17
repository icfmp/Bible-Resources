# MHC — exact long source-only spans outside their native chapter (same biblical book)

**Date:** 2026-11-17  
**Evidence:** [six-volume private pinned comparison run #44143021293](https://github.com/icfmp/Bible-Resources/actions/runs/44143021293), **all six volume jobs SUCCESS** on the exact same branch revision `b0d6a667a4e996c713d83bc7690c4ce682675958`. Also successful at this revision: Validate #44143021291, tool registry #44143021334, original native raw #44143021381, source-reference anchors #44143021369, private JSword #44143021296 and Xiphos startup/integrity #44143021267. The Xiphos job is **not** full commentary-pane GUI acceptance.

## What was actually searched

The existing source-neutral `OriginalExtraGapNativeChapterProbe` now separately scans other **same-chapter** and **different-chapter same-book** genuine SWORD K/I raw payloads during the full **32,355 native K/I/TOP frame replay**. It strictly removes only actual compiled XML `reference` label words, preserves unlinked source words and their exact original order and case, and searches *whole exact contiguous* extra spans of at least six words. Identical raw SHA repetitions do not constitute another independent text location. The six original CCEL XML source volumes and CrossWire MHC 2.2 were independently SHA-pinned and unchanged; only closed numerical categories and source/native identity hashes were exported.

| Original independent source unit | Actual CCEL extra *unlinked* word spans against selected same-start native payload | Other **same chapter** distinct native K / I | Other **chapters within same book** distinct native K / I | Whole-span exact hits in other same-book distinct K/I |
| --- | --- | --- | --- | --- |
| CCEL III `Bible:Ps.7.1-Ps.7.9`, original XML line **27749**, source reference SHA `f9a402dda0436aaed29b311707a672f1057df6e7bba16b58a43e5a1a91ac56a0` | **16** (KJV Psalm superscription) + **569** (separate expository `p` #6) | **1 K + 1 I** | **443 K + 150 I** | **0 of 2 spans** |
| CCEL VI `Bible:Acts.17.22-Acts.17.31`, original XML line **23188**, source reference SHA `f00b1d632a701e2617522eb9e214b3f6fa6b6547bbe836814a214636556ba06d` | **235** (separate expository `p` #17) | **4 K + 1 I** | **104 K + 28 I** | **0 of 1 spans** |

Original CrossWire same-start raw hashes: Psalm 7 `77f3d7bf9699b9cafadceabb62c8b192f554e485d997c85293666f38aa210ac4`; Acts 17 `eec29229b36ef7affda5dd8babfeb3c3417965058392bb2451798a90fb499db4`. Original source-body hashes: Psalm 7 `48809f08f932d9d68c4cbc56267a6ffdf973bf9bbafc9401d0916296824fb4ea`; Acts 17 `0d3f52a0c7cb4c29694995ecd920d3f4e1f95409e22df3f4025afbe12b51fb7d`.

**Confirmed negative witness:** neither *full exact contiguous source-only gap* is present in another distinct raw K/I payload elsewhere **in its original biblical book**, including every original K/I introduction. This extends the earlier same-chapter-only result. It is a much stronger **location** witness but **does not certify missing authored commentary**: the text might be split, paraphrased, embedded in linked labels/other markup, placed in another book, reflect an independently edited historical edition, or be present in an unevaluated duplicate same-start raw. The original same-start stock text does not contain the complete gaps by definition of the source-unique alignment, but neighboring partial fragments have not been exhaustively investigated.

The authentic original CCEL `p` boundary analysis independently identifies **569 unlinked words within 588 visible words** of Psalm 7 paragraph #6 (19 linked-label words), and **235 unlinked/visible words** in Acts 17 paragraph #17, with their original verse-range divisions intact. The smaller 16-word Psalm 7 paragraph #1 is independently a biblical KJV superscription and **must not** be mixed into Henry's exposition.

## Next controlled acceptance gate

1. Collate the *exact paragraphs* against independent scanned/proofread historical print witnesses including original wording, punctuation and references. The [Psalm 7 research](psalm7-1828-independent-expository-witness-2026-11-17.md) has a printed-lineage match by narrative sequence, **not** a token-perfect proof. The independently located printed Acts XVII opening is **not** proof of the paragraph's own text.
2. If needed, perform a bounded *whole-native-corpus* other-book search or partial-gap investigation with source-bound closed metadata; do not silently relocate sections or take a no-exact-match as entire-word absence.
3. Resolve electronic edition rights, printed historical authorial identity, original section ownership and independent reader GUI behavior before any candidate correction, merge or publication.

**No original CCEL word or punctuation, CrossWire K/I/TOP raw, original reference, source XML or public MHC package/catalogue/release was edited.** Draft PR #286 remains deliberately unmerged. The code extension is generic and covered by successful six-volume real-source tests; the next textual/editorial gates remain open.
