# MHCC 0.1.1 — Editorial and source-rights acceptance record

**Resource:** `mhcc-crosswire`, proposed released SWORD ID `MHCC`, curated edition `0.1.1`.

**Reviewed scope:** the exact historical CrossWire `MHCC` version `2.0` module (2021-02-14), original archive SHA-256 `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d`, plus *only* the two demonstrated source errata and the 24 navigation aliases that point at 17 existing unchanged sections. This is not a new Modern English adaptation, not the complete Matthew Henry commentary, and not a separate CCEL edition.

## Source and rights review (2026-11-16)

1. [CrossWire's official module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC) identifies Matthew Henry's Concise Commentary and explicitly gives **Distribution License: Public Domain**, with the provider's accompanying **Copy Freely** description. This module is the exact source actually fetched and pinned by SHA-256 for the rebuild. Public-domain status is an upstream declaration, not a separate copyright assignment or a claim that the Bible Resources project owns historical prose.
2. The commentary's historic author lived centuries ago. The source-specific CrossWire distribution declaration supports redistribution and editing of that attested digital text, subject to retaining truthful provenance and the original rights information. The edited release retains the `DistributionLicense=Public Domain` header; no CC0 claim is made for inherited source material.
3. [CCEL's copyright policy](https://www.ccel.org/about/copyright.html) describes separate restrictions or permissions for CCEL editions, special contents and republication. Its digitization was used solely for comparison, not as replacement prose, formatting, licensing or a source for undocumented editorial changes. No derivative rights over CCEL-specific contents are asserted.
4. The statement that the text matches a Moody Press 28th printing, and the roughly 1,200 earlier digital corrections, come from CrossWire's own historical module description. The edition preserves those statements as attributed upstream assertions; it does not certify correspondence with any physical printed copy.

## The exact reviewed edits

- **17 source-attested original sections, 24 new navigation addresses** linking to those same native section bodies. No redrawing of section boundaries or paragraph/poetry layout.
- **Ezekiel 3:** `3:12–2` → `3:12–21`, both visible citation and OSIS reference, on one original content body shared by 11 pre-existing verse addresses. The original can be reconstructed byte-for-byte from the reviewed erratum.
- **1 Chronicles 7:** `Zebulun or Dn` → `Zebulun or Dan`, limited to one original source entry, also reversible.
- All other original numbered commentary, introduction and TOP content remains native SWORD source-identical. No publication of the 25 unresolved CCEL/CrossWire cross-edition annotation differences; these are distinct editorial decisions.

**Independent full-source technical receipt:** original 28,718 numbered K plus 1,255 introduction I and two TOP; corrected 28,742 numbered K, same I/TOP; original raw corpus SHA-256 `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6`; corrected source corpus SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`; complete source proof SHA-256 `e51358a9b10185f2a45bbb63a38d6ccf063e8f492905f8519bf4ed9d54aaa7e4`. Four of four real Xiphos selected-passage tests passed. Every final release binary and date-dependent configuration must be rehashed against this record.

## Reader identity and editorial presentation

The project owner explicitly requested changing the **released SWORD identifier from `BRMHCC` to `MHCC`**. This collides by design with the original CrossWire ID. An installed CrossWire `MHCC` must be deliberately replaced; an old Bible Resources `BRMHCC` may remain installed and must be managed separately. No implicit uninstall, provider supersession or preference migration is claimed. Release notes document the difference. The earlier public `mhcc-0.1.0` release remains unmodified, including its original SHA-256.

**Version-specific reader description:** the 0.1.0 profile's old approval was for a different module ID and text scope; it must not be reused. Publication without an optional reader profile is supported; a separate reviewed English profile can be added later if explicitly approved. The SWORD `About` metadata is independently attributed and must include a revision date matching the actual versioned release.

## Owner authorization, boundaries, and remaining conditions

On 2026-11-16, the project owner explicitly authorized integrating the verified seven-file corrected candidate into [draft PR #275](https://github.com/icfmp/Bible-Resources/pull/275) and releasing MHCC 0.1.1 **after** final editorial, legal and technical checks (recorded in [issue #276](https://github.com/icfmp/Bible-Resources/issues/276#issuecomment-6923257588)). This authorization covers the bounded edition and version migration described above, not unrelated source changes and not a waiver of the independent final tests. It is not a personal legal opinion or a new licence issued by the owner.

**Release acceptance criteria:** exact seven files matching the reviewed corrected source; final SWORD `Version=0.1.1`, `SwordVersionDate` equal to the genuine publication date, original descriptive text attributed; one current `MHCC` catalogue entry, one corresponding immutable versioned GitHub Release and source-proof-bound plan; unchanged old 0.1.0 release and verified rollback; regenerated and checked public deterministic ZIP SHA-256; one successful build/validate/reader audit on the actual final commit; no false equivalence to the original upstream binary or CCEL digitization.

This is a transparent provenance and bounded-edition review record. The final release is not declared live by the existence of this document; the actual GitHub Release, package and catalogue endpoints must be checked separately after the publication workflow runs.
