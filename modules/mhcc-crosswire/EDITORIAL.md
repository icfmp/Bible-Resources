# Matthew Henry Concise Commentary — Bible Resources 0.1.0

**Curated source:** the exact existing CrossWire `MHCC` 2.0 compiled SWORD
`zCom` module (2021-02-14), **not** the complete `MHC` and **not**
a rebuilt or harmonized CCEL transcription.

## Reviewed editorial and rights decision — 2026-11-14

The project owner directed publication preparation of this exact-source
commentary and selected the most permissive lawful distribution available
for the project's own original contributions. The exact CrossWire witness
explicitly declares `DistributionLicense=Public Domain` and
"Copy Freely" on the [official module record](
https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC).
This source-specific declaration is retained unchanged; Bible Resources
does **not** claim to relicense CrossWire's stock payload under CC0.
The public-domain claim is positive CrossWire source evidence, not
independent reconstruction of every correction in the digital edition.

The source metadata attributes the text to a Moody Press 28th printing
(ISBN 0-8024-5190-X), via a previously digitized version with about
1,200 editorial corrections. This project **does not guarantee**
word-for-word historical print equivalence. The independently downloaded
CCEL XML differs in some original annotation and wording, and is **not
copied into this release**; these differences are not corrected by guessing.

## Reproducible exact-stock transformation

- Original archived CrossWire `MHCC.zip` SHA-256:
  `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d`.
- Original upstream `mhcc.conf` SHA-256:
  `2762a04757ec3ee14bcf5d442fedcd47d2b938d573de4e9100a31aa073bc5863`.
- Independent full 29,975-key native SWORD raw-corpus SHA-256:
  `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6`.
- Final SWORD module ID: `BRMHCC`, preserving the original `zCom`
  driver, KJV versification, all 6 compressed data files **byte-for-byte**,
  all original 29,975 occupied native entries and exact source XML markup.
- **Only** the curated SWORD header (`MHCC` → `BRMHCC`),
  matching `DataPath`, and distribution `Version=0.1.0` (replacing
  upstream `2.0`) differ from the original `.conf`. The CrossWire
  provenance, licence, citation data, original edition description,
  and compiled text are preserved.
- Final archive/Pages catalogue SHA-256 must be independently verified
  after staging and deployment; an earlier preflight-only `BRMHCC`
  archive using upstream `Version=2.0` has a different SHA and is
  **not** the final curated `0.1.0` package.

## Technical verification and limited reader acceptance

- Real SHA-attested full private candidate `BRMHCC` and CrossWire
  stock identity: [PR #261](https://github.com/icfmp/Bible-Resources/pull/261).
- Full native XML inventory: all **29,973** K/I original fragments
  strict-parsed, 2 opaque TOP records, all **10,557** source references
  have an `osisRef` and a visible label, and all **15,985** source
  titles have content: [#258](https://github.com/icfmp/Bible-Resources/pull/258),
  [#260](https://github.com/icfmp/Bible-Resources/pull/260).
- Actual Xiphos **4.2.1** reader + independently verified Bible:
  **5/5** selected original commentary passages read back correctly,
  and **2/2** original source reference labels and href destinations
  preserved in the real GUI: [#224](https://github.com/icfmp/Bible-Resources/pull/224).
- The project owner explicitly accepted this **representative reader
  smoke-test scope** for publication preparation on 2026-11-14:
  [#257](https://github.com/icfmp/Bible-Resources/issues/257).
  Actual mouse-link navigation, exact heading typography in every
  reader and modern Android/other-Xiphos-version GUI output remain
  **NOT VERIFIED**. Those are **not** assertions of a stock source defect.

## Installation and corrections

The package is intended for normal SWORD readers as a regular
`mods.d/brmhcc.conf` plus `modules/comments/zcom/brmhcc/`.
The final immutable release ZIP checksum will be recorded after
generation. The HTTPS catalogue uses the curated `BRMHCC` ID;
the original CrossWire module remains independently available.

Report genuine source discrepancies with the original location and
the exact upstream/curated module version. Reader rendering defects
should not cause unreviewed edits to authorial words, punctuation,
headings, notes or scripture targets.

## Status

The final module source is approved for this exact **compiled-stock,
no-authorial-text-change** route. This document is not by itself proof
that a public ZIP is deployed; public URLs/asset SHA and catalogue
delivery require a successful independent deployment verification.
