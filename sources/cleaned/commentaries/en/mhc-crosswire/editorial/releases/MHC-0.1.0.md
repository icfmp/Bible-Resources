# MHC 0.1.0 — Matthew Henry's Complete Commentary

Complete English six-volume commentary on the whole Bible, based on CrossWire's MHC 2.2 official authoring OSIS. This is **MHC**, not the concise MHCC.

Bible Resources preserves the original authorial commentary prose, 4,256 source bodies and 7,073,234 word tokens. This technically reviewed release repairs 25 source-attested Scripture cross-reference targets, supplies the independently reviewed Romans 4 whole-verse indexing, and exposes the 2 Chronicles 1 introduction using native SWORD introduction semantics. All transformations are documented and reversible.

The released module uses the standard SWORD **zCom4** commentary format, KJV versification, SWORD identifier `MHC`, and curated version `0.1.0`. Reader tests included independent native readback and representative real Xiphos passages. Individual hyperlink click behavior in every GUI has **not** been certified.

## Important installation identity

**CrossWire already distributes another module named `MHC`**, upstream version `2.2`. Only one SWORD module with the same ID may be installed in a given SWORD module directory. Choose the provider explicitly; installing Bible Resources `MHC` means replacing the CrossWire module if it is already present. Do not assume `0.1.0` will automatically supersede upstream `2.2` in numerical version comparisons. MHCC is a separate concise commentary and remains unchanged.

## Source, provenance and permissions

- CrossWire official [MHC 2.2 information and Public Domain declaration](https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC).
- Official authoring OSIS: [CrossWire's MHC GitLab repository](https://gitlab.com/crosswire-bible-society/mhc) at `537591a94c991941877b47a06666b6a7812e05d8`.
- Original authoring source SHA-256: `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`.
- The CrossWire source credits the Christian Classics Ethereal Library (CCEL) and Logos Research, Inc. These credits are preserved. CCEL's separate electronic transcription was a comparison witness, not silently inserted into the release.
- Original compiled upstream package SHA-256: `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`.

Project-owner source rights and publication decisions dated November 19, 2026 are tracked in [issue #285](https://github.com/icfmp/Bible-Resources/issues/285). A public-domain declaration from CrossWire is used as the distribution basis; no project re-licensing of inherited text is claimed.

The immutable versioned release asset is `MHC-0.1.0.zip`; the continuously served catalogue download is `sword/packages/MHC.zip`. The final SWORD `.conf` includes a single provenance-only `TextSource` line added to the reviewed artifact; this is recorded with reversible original/new hashes in the editorial record and does not alter any compiled commentary bytes. The published ZIP checksum is pinned in the official release plan and must match the catalogue.
