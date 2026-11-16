# MHCC 0.1.1 — Matthew Henry's Concise Commentary

This is the source-reviewed Bible Resources edition of the **original CrossWire MHCC 2.0** digital commentary. The commentary text is in English, covers 66 Protestant biblical books, and is distributed as a standard SWORD `zCom` commentary (KJV versification, `BlockType=CHAPTER`).

## Corrections and navigation

- Added **24 native SWORD navigation links** to 17 already existing authorial sections. No commentary section was subdivided, merged, invented, deleted or moved.
- **Ezekiel 3:** corrected the demonstrable malformed citation and its OSIS target from `3:12–2` to `3:12–21` within one original section body shared by 11 existing verse keys.
- **1 Chronicles 7:** corrected one digital transcription error, `Zebulun or Dn` → `Zebulun or Dan`, in one original commentary entry.

The source and native SWORD attestation covers **28,718 original numbered keys, 1,255 book/chapter introductions, and two opaque TOP entries**. Exactly 24 additional keys are linked to existing sections, and precisely 12 original numbered key addresses contain the two audited corrections. All other original authorial commentary text, markup, section boundaries and native linked identity are preserved. Representative selected passages passed a real Xiphos reader test. This is not a claim that every third-party viewer formats the commentary identically.

## Important: SWORD module name changed

This release uses the SWORD ID **`MHCC`**, instead of the previously curated **`BRMHCC`** ID. This was an explicit project-owner decision, but it changes installation behavior.

- **Existing Bible Resources `BRMHCC` installations** are not automatically removed when the new `MHCC` edition is installed. Remove the old `BRMHCC` module explicitly when appropriate; do not assume its reader preferences or other saved per-module state will migrate.
- **CrossWire's own `MHCC` module already uses the same SWORD ID**, with upstream version `2.0`. A single SWORD installation cannot hold both under that exact identifier. Select and replace the desired provider deliberately; the curated `0.1.1` numbering does not imply that an independent upstream `2.0` version comparator will consider it newer.
- The versioned GitHub release artifact is **`MHCC-0.1.1.zip`**. The current Bible Resources catalogue download is **`sword/packages/MHCC.zip`**, not the former `BRMHCC.zip`.
- The preserved **[BRMHCC 0.1.0 release](https://github.com/icfmp/Bible-Resources/releases/tag/mhcc-0.1.0)** remains available independently for recovery. Its original files and checksums were not changed.

## Attribution, edition provenance and distribution rights

- Source: [CrossWire / SWORD Project, module MHCC 2.0](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC), dated 2021-02-14.
- The upstream module's distribution declaration is **`Public Domain — Copy Freely`**. Bible Resources preserves this declaration and does not purport to relicense the CrossWire source text or notes under CC0.
- CrossWire's historical attribution to a Moody Press 28th printing is reported as **CrossWire's attribution**. Bible Resources has not independently proved exact print-edition identity.
- The separate CCEL digitization was comparison-only evidence. No text, XML markup or specially edited content was copied from it into the new module; see [CCEL's distinct copyright policy](https://www.ccel.org/about/copyright.html).
- Editorial details and the exact source/native SWORD integrity record: [issue #274](https://github.com/icfmp/Bible-Resources/issues/274), [the preparation and publishing decision #276](https://github.com/icfmp/Bible-Resources/issues/276), [Ezekiel issue #277](https://github.com/icfmp/Bible-Resources/issues/277), [1 Chronicles issue #279](https://github.com/icfmp/Bible-Resources/issues/279).

The original CrossWire archive remains pinned by SHA-256 `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d`. The corrected complete native corpus is pinned by SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`. The public release's full ZIP checksum must agree exactly with the reviewed GitHub Release plan and current catalogue.

This edition was prepared for publication only after the project owner's explicit 2026-11-16 authorization, and only after the independently checked source, rights, title, version, module identity and package bytes meet the publication gates.
