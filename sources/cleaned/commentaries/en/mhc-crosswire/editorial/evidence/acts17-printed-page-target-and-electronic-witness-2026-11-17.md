# MHC Acts 17:22–31 — precise historical print-page target and witness classification

**Date:** 2026-11-17  
**Parent:** [MHC intake #285](https://github.com/icfmp/Bible-Resources/issues/285); [draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286)  
**Status:** source and folio provenance only; **not** a token-perfect printed paragraph collation or correction approval.

## The exact original-source anomaly under examination

- Original six-volume CCEL ThML witness **Volume VI**, `Bible:Acts.17.22-Acts.17.31`, XML line **23188**.
- Original full `scripCom` reference SHA-256 `f00b1d632a701e2617522eb9e214b3f6fa6b6547bbe836814a214636556ba06d`; full original adjacent body SHA-256 `0d3f52a0c7cb4c29694995ecd920d3f4e1f95409e22df3f4025afbe12b51fb7d`.
- The source-extra **235 unlinked/visible Unicode word** span is one whole original CCEL **`p` #17 of 22**, exact source-visible ordered word digest `462ec448acf7e29788eeedfbb245ad08ea98faaade8c0dbef7755c042d2779cc`. CrossWire selected original SWORD raw SHA `eec29229b36ef7affda5dd8babfeb3c3417965058392bb2451798a90fb499db4`.
- Original source and stock were SHA-pinned, compared without edits; [whole- and partial-span audit #44145831775](https://github.com/icfmp/Bible-Resources/actions/runs/44145831775) passed **6/6 volume jobs**. No whole extra paragraph in another distinct Acts K/I raw; one other-book-chapter K raw contains a **7-word** exact source-gap fragment. This does not establish historical authorial omission or printed edition identity.

## Concrete historical facsimile locator, not merely a chapter index

The scanned [Wikimedia Commons Volume VI DJVU](https://commons.wikimedia.org/wiki/File:An_Exposition_of_the_Old_and_New_Testament_(1828)_vol_6.djvu) is the **undated Barrington & Haswell reprint** of the 1828 Towar & Hogan edition lineage, not an authenticated original 1828 impression. [Wikisource's edition note](https://en.wikisource.org/wiki/An_Exposition_of_the_Old_and_New_Testament_(1828)) explicitly explains this reprint relationship, including known wording corrections elsewhere.

The [Volume VI page index](https://en.wikisource.org/wiki/Index:An_Exposition_of_the_Old_and_New_Testament_(1828)_vol_6.djvu) exposes the print-page/DJVU-frame offset: for the **Acts 17 sermon**, printed page **179** corresponds to DJVU **frame 185**; print pages **180–183** correspond to DJVU **frames 186–189**. The section is independently located in the scanned-page text presentation of the separate [Psalms/Acts 1828-lineage facsimile hosted by Digital Puritan, *Acts* PDF](https://www.digitalpuritan.net/Digital%20Puritan%20Resources/Henry%2C%20Matthew/An%20Exposition%20of%20the%20Old%20%26%20New%20Testament%20%28Ind%20Files%29/%5BMH%5D%20Commentary%20on%20Acts.pdf), which displays the Acts XVII sermon at printed **p. 179** and changes to the Acts XVIII heading at **p. 184**. Its OCR/text layer is interleaved two-column extraction and **cannot** certify exact wording or punctuation; direct PDF screenshot retrieval failed because of its large file size. This checkpoint therefore **does not** claim visual page-by-page verification of p #17.

The DJVU index marks the target printed-page transcription links **red/unproofread**. Therefore the fact that an Acts XVII scan exists, plus that a publisher's text layer shows the sermon, is **not proof that CCEL's exact 235 words are in the facsimile**. The exact 235-word paragraph must be located on the individual facsimile leaves and inspected, distinguishing original author's words from printed-editor insertions.

## Independent digital-text comparison scope

- [CCEL current rendering of Acts 17, verses 22–31](https://ccel.org/ccel/henry/mhc6/mhc6.Acts.xviii.html), an electronic rendering of the original pinned digital source *family*, not an independent print witness.
- [Wikisource's separate *Matthew Henry's Commentary on the Whole Bible*, Volume VI / Acts Part 2](https://en.wikisource.org/wiki/Matthew_Henry%27s_Commentary_on_the_Whole_Bible/Volume_6/Acts_Part2) reproduces the continuous Acts XVII 22–31 sermon (e.g. the transition from pagan poets to the argument against idolatry and the final appeal to repentance). Its exact **edition and textual ancestry remain unverified**, so agreement with CCEL does **not** constitute an independently authenticated 1828 print paragraph, and it may stem from the same prepared electronic text.
- A modern born-digital ["Commentary on the Whole Bible, Volume VI" PDF](https://grace-ebooks.com/library/Matthew%20Henry/MHry_Commentary%20on%20the%20Whole%20Bible%20VOL%206%20act-Rev.pdf) reproduces the Acts content, but **is not a substitute for eighteenth- or nineteenth-century authenticated printed folios**.

## Narrow next gate (before any editorial proposal)

1. Consult the authenticated original printed leaf-images **DJVU 185–189** (printed pages 179–183) and locate the passage matching original CCEL **`p` #17**. Preserve left/right column order and include the full transition before and after the paragraph.
2. Reconcile **the exact case-sensitive 235 Unicode tokens**, spelling, punctuation, embedded quotations, authorial section boundaries, and any references against the pinned original XML paragraph; record line/page and discrepancies without reproducing unlicensed electronic XML wholesale.
3. Independently check the exact same-start CrossWire native payload and all other relevant original K/I entries before designing a reversible, separately approved correction. This check is **more specific** than a matching sermon/chapter heading.
4. Confirm exact electronic edition rights for any reused CCEL/Logos markup or annotations, and retain separate real-reader GUI acceptance.

**No original XML, commentary prose, punctuation, native verse reference or CrossWire binary was altered. No corrected MHC, publication, digital permission or catalogue claim follows from this evidence.** Draft PR #286 stays unmerged.
