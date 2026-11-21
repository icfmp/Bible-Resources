# Louis Segond 1910 — Bible Resources 0.1.0

First public, **initial** SWORD module. Editorially authorized by the project owner on 2026-11-09 after tests with AndBible and comparison against the official eBible module. This is **not** an assertion that every passage has been visually inspected.

## Source and independently reproducible evidence

- Original edition: **Louis Segond 1910**, eBible `fraLSG` / `fraLSG1910eb`.
- Publisher: https://ebible.org/Scriptures/details.php?id=fraLSG
- Publisher public-domain declaration: https://ebible.org/fraLSG/copyright.htm
- Original USFM ZIP SHA-256: `64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900`.
- Original USFX ZIP SHA-256: `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`.
- Original extracted USFX SHA-256: `90a53c3a61f0c07a329d8fc19c593b8c353f2b3e5a6830dbf4c53d2b08fd2141`.
- Reproducible full-corpus engine audit: https://github.com/icfmp/Bible-Resources/actions/runs/42632394004
- Full candidate source, transformations and audit suite: https://github.com/icfmp/Bible-Resources/pull/24 at commit `7f675b4d621e5c0aba5fd78f0cb3cb468eb2cd26`.
- Immutable approved input package `BRLSG1910Preview3.zip`, SHA-256:
  `053b65d73d39f4268610ca743cccb605baff8860a612d7a987b99273bca3807e`.
- Stable release archive `BRLSG1910-0.1.0.zip`, SHA-256:
  `af2f80ea84f40a6bf62993c9e65c2e2061e1ec20b34b0772a4eb775dd47723c1`.
- This stable release **reuses all four verified SWORD binary data files byte for byte**.
  Only the SWORD ID, relative directory name and independently reviewed `.conf` change.
- Driver: **standard SWORD RawText**, SourceType OSIS, Encoding UTF-8, Versification **Segond**, module ID `BRLSG1910`. It is not an eBible or CrossWire official module.

## Quality results

The independently tested candidate preserved, in the full 66-book source:
- 705,728 ordered Strong/lemma-associated source word elements.
- 9,751 note bodies, callout identities and book-global word-relative anchors.
- All authored Scripture words/punctuation in the source comparison and all cross-reference text.
- Structural opening/closing positions of titles, paragraphs, poetry and quotations.

These checks support lexical/source correctness, **not exact original typography** of every note. The owner has accepted an initial release with openly disclosed layout differences, to be refined based on actual reading.

## Known limitations and instructions for readers

1. The original eBible source has both **Mark 10:52 and 10:53**. The stock stable `Segond` registry lacks separate Mark 10:53: **the entire two-verse source text is in one readable key, Mark 10:52**. This is an explicitly owner-approved, reversible index compromise. No words are removed and the source is never changed. Some readers show only the number 52, despite the preferred editorial label `52–53`.
2. eBible source has no separate authored Job 34:37 key; no fabricated source verse is supplied. The empty registry slot is not an authorial verse.
3. Footnote whitespace and some table/introduction rendering are not typographically identical to the original USFX. Three residual literal `\\i` sequences in introduction tables remain for follow-up. Biblical verse wording is not rewritten.
4. Some original heading parallel references lack explicit machine-readable targets. This release preserves the exact authored text without presenting those specific headings as false clickable hyperlinks.
5. Android **AndBible** visual testing found the module usable as a standalone translation. A side-by-side comparison with official eBible can display false missing verses due to the two modules declaring *different* versifications; the application Bible's verse-alignment issue is documented at https://github.com/icfmp/Bible/issues/252. Do not attribute this to missing text without examining the underlying SWORD entries.
6. **Xiphos desktop rendering has not been visually certified**. Standard released SWORD engine and isolated `diatheke` tests passed. Report reader-specific problems before changing any source text.

## Installation

Extract the release ZIP into an appropriate SWORD module home (it contains the normal `mods.d/` and `modules/` entries), or use a reader's supported SWORD ZIP import. This module deliberately uses its own ID so it does not overwrite the eBible version.

To verify the archive:

```sh
sha256sum BRLSG1910-0.1.0.zip
```

Expected SHA-256: `af2f80ea84f40a6bf62993c9e65c2e2061e1ec20b34b0772a4eb775dd47723c1`.

Please report passage-specific editorial or reader issues to https://github.com/icfmp/Bible-Resources/issues ; quote the exact verse, reader, module version and screenshot, but do not silently alter source transcription.

## Release scope

This is a small, honest first publication intended for broader reading and review. It does not close the remaining upstream investigation (https://github.com/icfmp/Bible-Resources/issues/26), the independent visual review (https://github.com/icfmp/Bible-Resources/issues/25), or the historic print-edition comparison. Source and transformed data retain separate identities and checksums. Future updates must not silently replace the `0.1.0` artifact.
