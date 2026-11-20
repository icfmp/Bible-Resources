# MHC 0.1.0 — Matthew Henry's Complete Commentary (DRAFT — NOT RELEASED)

**Status: private publication candidate only.** This document does not authorize publication, contain a compiled SWORD module, or assert a final package SHA-256. It must not be placed in the downloadable catalogue until the project owner authorizes release.

## Source, identity and provenance

Bible Resources' proposed first edition is sourced from **CrossWire MHC 2.2** (the complete commentary, **not MHCC**). The full original authoring OSIS is pinned to CrossWire GitLab revision `537591a94c991941877b47a06666b6a7812e05d8`, original SHA-256 `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`.

The proposed SWORD module ID is **`MHC`**, English, KJV versification, `zCom4` commentary with OSIS source. Proposed first Bible Resources edition version is **0.1.0** (not yet authorized or built under a public module identity).

## Verified source-preserving improvements

- Original word streams, punctuation, section titles, paragraphs, note texts and visible citation labels are preserved from the exact CrossWire original source.
- 25 machine-only Scripture cross-reference targets have reviewed source/label-backed corrections. No display wording was replaced.
- Romans 4, overlapping source verse-group navigation and several shared section boundaries were adjusted in reversible OSIS machine scope, retaining every original source commentary body.
- A wrongly verse-indexed chapter preface at 2 Chronicles 1 is now a genuine **native chapter introduction**. The separate verse exposition remains intact. Its authentic preface was recovered in a real Xiphos *chapter-heading context menu*; it does not appear in an ordinary verse-selection clipboard.
- The real native SWORD readback contains **31,098 numbered locations, 1,255 introductions and two TOP frames**, with all **4,256 original authored bodies** verified. Three substantial comments were also read from a genuine GTK Xiphos GUI; pinned AndBible JSword indexing checks succeeded.

This means source-content/structure integrity and representative reader text reception have passed. It **does not** claim that every reader renders original notes and layout alike, nor that Xiphos mouse-click navigation to every compound cross-reference has been verified.

## Upstream rights and attributions

The project owner has explicitly chosen CrossWire's official **`Public Domain — Copy Freely`** distribution declaration for MHC 2.2 as the project's licensing basis. This edition retains CrossWire's source credits for the **Christian Classics Ethereal Library** and **Logos Research, Inc.**, without claiming to relicense the original authorial text. See [official CrossWire MHC module page](https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC).

## Important: same SWORD module identifier as upstream

**CrossWire already distributes another module named `MHC` (version 2.2).** SWORD installations cannot install two independently managed versions of the same ID without replacement. Replacing CrossWire MHC with a Bible Resources `MHC` edition therefore requires an explicit user/provider selection. A version string **0.1.0 is numerically lower than upstream 2.2** and must not be represented as an ordinary automatic upgrade.

The first version number, title, module packaging, catalogue provider behavior and replacement messaging are provisional until final owner signoff. No change to the `icfmp/Bible` application is part of this draft.

## Unfinished release-only gates

- [ ] Record the final private ZIP build's reproducible, independently reinstalled SWORD source/readback evidence (never store a private trial ZIP as a public artifact).
- [ ] Establish actual clicked-reference navigation or explicitly document the supported boundary of the reader tests. Review representative note/title/paragraph rendering.
- [ ] Complete final production-module metadata, identity/update semantics and immutable package SHA-256.
- [ ] Reconcile and independently revalidate the draft PR against current `main`.
- [ ] Obtain **explicit final owner authorization** to merge and publish, then update catalogue/release notes and publish a verified archive in a distinct release step.

**Do not publish from this draft.** Track status in [issue #285](https://github.com/icfmp/Bible-Resources/issues/285), [PR #286](https://github.com/icfmp/Bible-Resources/pull/286) and the [private readiness receipt](../evidence/private-release-readiness-2026-11-19.json).
