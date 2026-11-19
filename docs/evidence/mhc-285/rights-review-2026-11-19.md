# MHC 2.2 — exact-edition digital redistribution rights review (2026-11-19)

**Decision: HOLD.** This is source-oriented due diligence, **not legal advice and not authorization** to publish original, cleaned or corrected OSIS/SWORD files. The privately compiled candidate and textual contents remain outside GitHub.

## Precisely identified proposed work

- SWORD module: CrossWire **MHC 2.2**, released **2022-08-29**, type `zCom4`, English; original authoring OSIS pinned to the exact CrossWire GitLab authoring commit and SHA-256 in `config/commentary-intake/mhc-crosswire.json`.
- Editorial scope: source-preserving removal of truly inert display artefacts; 25 independently source-attested reference-attribute corrections; 2 Chronicles 1 chapter-title metadata and chapter-introduction classification; source-authored first/second section ownership (including Romans 4). No rewritten Matthew Henry prose. All transformations and published binary remain subject to approval.
- Proposed distribution is a **modified independent digital edition**, not merely a hyperlink to CrossWire's official existing MHC. Source, downstream module, notes and accompanying editorial improvements therefore require explicit review of applicable rights/provenance.

## Evidence and precise limits

1. **CrossWire official MHC listing**, https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC — lists distribution license **Public Domain** and the module's version 2.2; explicitly attributes the electronic text preparation to **CCEL**, with a further credit to **Logos Research, Inc.** as a text provider. This is positive provenance/rights evidence, but the listing alone does not document a separate grant covering our modified electronic derivative.
2. **CCEL current copyright policy**, https://www.ccel.org/about/copyright.html — acknowledges that many underlying books are public domain, but warns that added introductions, images and other special digital/editorial contents may have separate protection; expressly requests contact for permission to republish CCEL works (even though some personal/educational/nonprofit uses are allowed). Applicability to the exact CrossWire OSIS-derived edition must be established rather than guessed.
3. **Debian bug #883932**, https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=883932 — contemporaneous Aug 2021 packaging correspondence documents that a previous `sword-comm-mhc` upload was **rejected over uncertainty about CCEL's copyright terms**, and the upload was considered DFSG-incompatible at that time. This does **not** automatically decide rights for CrossWire 2.2 (2022); it is significant documented evidence that the apparent public-domain labeling has been contested for the electronic edition.
4. **CrossWire SWORD announcement**, https://crosswire.org/pipermail/sword-devel/2022-May/049160.html — official May 2022 MHC 2.1 update announcement describes repairs to multiple cross-references. Confirms a distinct CrossWire editing history, relevant when identifying whose machine/reference annotations are included in a derivative.
5. **CrossWire module submission guidance**, https://wiki.crosswire.org/DevTools:Modules — calls for provenance and distribution permission for copyrighted text and requires license/source metadata. We should retain the full evidence chain rather than treating the public-domain status of Henry's eighteenth-century writing as blanket permission for all later digital additions.

## Release gates (intentionally not satisfied yet)

- [ ] Determine and document precisely which existing edition/typography/introductory material belongs to Henry's original public-domain text and which belongs to CCEL, Logos or CrossWire's later digital assembly/editorial additions.
- [ ] Obtain or document sufficiently specific, attributable **redistribution and modification permission** for the exact electronic source and downstream SWORD derived from it. If necessary, ask CCEL/CrossWire rights maintainers with the pinned MHC 2.2 identity and our explicitly bounded edits. Do not infer permission merely from public availability or noncommercial intent.
- [ ] Check territorial applicability, notably distribution to French and international users, and record the reviewed publication license/attribution obligations in a release manifest.
- [ ] Obtain project owner/editorial approval after source-fidelity and real-reader coverage have been reviewed independently.
- [ ] Only after approvals, decide whether to commit a cleaned OSIS master to `sources/cleaned/mhc/`, publish a SWORD release, or instead contribute verified repairs upstream to CrossWire.

## Current technical state (not rights approval)

- [Full private SWORD + real Xiphos run #44517068698](https://github.com/icfmp/Bible-Resources/actions/runs/44517068698): source-native reconstruction, verified 2Chr 1 introduction mapping and **three actual Xiphos commentary excerpts** succeed.
- The Xiphos run establishes no clicked-link navigation, Psalm 60 superscription highlight, full chapter-introduction GUI presentation or Android GUI signoff; see tracking comments in PR #286/issue #285.

**Hard stop:** `rights.status=research_only`, `owner_approved=false`, `digital_corrections_and_derivatives_reviewed=false` must remain unchanged pending actual evidence and approval. No source or binaries are published by this document.
