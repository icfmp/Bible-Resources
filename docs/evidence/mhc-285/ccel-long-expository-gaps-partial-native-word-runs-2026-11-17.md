# MHC — independently verified partial prose fragments of two large source-only paragraphs

**Date:** 2026-11-17  
**Scope:** research-only comparison of original SHA-pinned CCEL ThML with unchanged CrossWire MHC 2.2 native K/I text. No words or native keys published.  
**Exact audited code revision:** `b437503774b16c871a2da8af4e22da7752464339` in [draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286).  
**Real six-volume CI:** [run #44145831775](https://github.com/icfmp/Bible-Resources/actions/runs/44145831775): **6/6 original source volume jobs SUCCESS**, independent USFM title witness PASS. Other same-commit checks **8/8 PASS**: Validate #44145831639, tool registry #44145831182, raw native stock #44145831235, CrossWire/CCEL intake #44145831664, XML witness #44145831592, original reference anchors #44145831469, JSword private engine #44145831088, and Xiphos startup/integrity #44145831098. These are **not** a real corrected commentary-pane GUI/Android acceptance.

## Method

A generic extension of the existing `OriginalExtraGapNativeChapterProbe` reuses the already authenticated entire **32,355-entry original SWORD raw corpus replay**. For the two independently identified, source-authenticated, uniquely ordered original *unlinked* extra spans of 100 or more words, the probe finds exact **case-sensitive Unicode** contiguous token runs of **at least six words** in genuinely distinct raw K/I payloads *elsewhere in the same biblical book*.

- **Excluded from source-only prose:** only actual original ThML `scripRef` label text, not authored quotations, explanations, headings or notes.
- **Excluded from compiled prose:** only actual original SWORD XML `reference` label text, not arbitrary guessed word ranges.
- Count each *distinct native raw SHA* within the same chapter or other-chapter scope once, ignoring repeated K addresses to the selected raw body as independent evidence. The two scopes are reported separately; a shared identical raw body between scopes is not claimed as two independent manuscripts.
- Record only original XML line/ref/body SHA, selected native raw SHA, source-gap lengths, checked distinct native K/I counts, exact whole-gap hits, distinct other native bodies containing a six-word contiguous anchor, and the maximum exact contiguous run length of each source gap in those bodies. No original words, text excerpts or original native key strings are exported.
- Strict tests demonstrate a six-word partial match is *not* misreported as a full paragraph, a five-word run is below threshold, a different biblical book is excluded, and authentic source hashes are required.

## Proven same-book partial-run results

| Original CCEL source unit and exact SHA-backed identity | Source-only *unlinked* gap(s) | Actual distinct **other-chapter** native K/I payloads examined | Other-chapter distinct K/I payloads with ≥6 exact contiguous source-gap words | **Longest** original source-gap exact contiguous word run in another native payload | Exact entire extra-span in other original same-book K/I raw |
| --- | --- | --- | --- | --- | --- |
| III `Bible:Ps.7.1-Ps.7.9` (original XML line **27749**, full reference SHA `f9a402dda0436aaed29b311707a672f1057df6e7bba16b58a43e5a1a91ac56a0`) | **16** (independently verified biblical superscription, source p#1) + **569** (independent exposition p#6, **588** visible words incl. 19 linked-label words) | **443 K + 150 I** | **5 K, 0 I** | **0** for the 16-word title; **8** for the 569-word expository gap | **0** |
| VI `Bible:Acts.17.22-Acts.17.31` (original XML line **23188**, full reference SHA `f00b1d632a701e2617522eb9e214b3f6fa6b6547bbe836814a214636556ba06d`) | **235** (independent expository p#17, no linked labels) | **104 K + 28 I** | **1 K, 0 I** | **7** words | **0** |

For both original cases, distinct other raw payloads **within the same native chapter** also contained **zero** contiguous source-gap token runs of six words or more, and **zero** whole-span matches. Across the full original complete native raw corpus replay, no new original source text was injected, moved or altered.

The original source-body hashes (not copies of text) are:
- Psalm 7 `48809f08f932d9d68c4cbc56267a6ffdf973bf9bbafc9401d0916296824fb4ea`; native selected raw `77f3d7bf9699b9cafadceabb62c8b192f554e485d997c85293666f38aa210ac4`.
- Acts 17 `0d3f52a0c7cb4c29694995ecd920d3f4e1f95409e22df3f4025afbe12b51fb7d`; native selected raw `eec29229b36ef7affda5dd8babfeb3c3417965058392bb2451798a90fb499db4`.

**Interpretation:** The prose exists in separate original CCEL `p` units, but only very short, non-exclusive exact snippets appear elsewhere in the *same biblical book* in the unchanged CrossWire stock. This is strong source/stock **negative textual-location evidence**; it greatly weakens a theory that those paragraphs were simply copied intact or substantially verbatim into another chapter's K/I entry. It does **not** prove a historically authorial original paragraph is completely missing from all editions of the SWORD work, nor resolve whether actual CCEL XML prose corresponds to the historical printed edition: passages can be reworded, split, embedded in otherwise linked XML, placed in another book, altered in a digital preparation, or already partially represented in the selected original compiled slot outside the strict extra-gap alignment.

## Remaining correction gates (do not auto-repair)

1. Independently collate **the exact CCEL Psaume 7 original p#6 (588 visible words, 19 linked labels)** against the verified printed-edition scan and punctuation/reference markup. The [1828-derived printed witness](psalm7-1828-independent-expository-witness-2026-11-17.md) presently confirms historical exposition by sequence, **not exact 569-token identity**.
2. Locate and independently collate **the Acts 17 original p#17 (235 visible words)** in an independently scan-validated historical print. A [volume-VI Acts chapter witness](https://en.wikisource.org/wiki/Page:An_Exposition_of_the_Old_and_New_Testament_%281828%29_vol_6.djvu/178) is **only a chapter-opening witness**, not a proof of this paragraph.
3. Establish original source authority, CCEL/Logos digital edition modification/redistribution rights, the exact historical 1721/1828 reprint lineage, authorial sections and actual reader GUI presentation/navigation before proposing source-grounded reversible corrections.
4. Independently triage the original Psalm 8:1–2 source/native word-order difference. [Public wording variants](psalm8-public-edition-wording-collation-2026-11-17.md) already show historical edition differences, but do not yet identify which of these CrossWire uses.

**No edits to any original commentary prose, punctuation, SWORD native K/I/TOP, source XML, scripture reference, module/metadata, catalogue, licence, package or release.** [Draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286) remains unmerged. The newest **documentation-only commit**, if any, must not be mistaken for a new full-source CI PASS until its own checks complete.
