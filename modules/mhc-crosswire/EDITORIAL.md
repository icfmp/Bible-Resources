# MHC 0.1.0 — source and editorial publication record

**Edition:** Matthew Henry's *Complete Commentary on the Whole Bible*, based on CrossWire's **MHC 2.2**, not MHCC. The published module is a source-preserving, corrected OSIS/SWORD **zCom4** reconstruction, **not** the byte-identical 2.2 upstream package.

**Original provenance:** CrossWire's official [authoring source](https://gitlab.com/crosswire-bible-society/mhc) commit `537591a94c991941877b47a06666b6a7812e05d8`, original `mhc.osis.xml` SHA-256 `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`. Original compiled 2.2 ZIP SHA-256 `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`. Independent six-volume CCEL witness was used for comparison; CCEL material was not silently substituted. Attribution to CrossWire, CCEL and Logos Research, Inc. is preserved.

**Publisher rights:** The project owner accepted the official [CrossWire MHC 2.2 Public Domain — Copy Freely declaration](https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC) on 2026-11-19, without re-licensing original prose. Publication and source-derived technical corrections were expressly requested. This is a project source-rights decision, not an independent legal certification.

## Reviewed technical/editorial scope

- 4,256 source commentary bodies and 7,073,234 source word tokens retained, with source, markup and native checks.
- 25 verified OSIS cross-reference target repairs, each source-line/hash-backed and reversible; source labels, authorial wording, quotations and notes preserved. Psalm 60 superscription conservatively links to the chapter, never a fabricated verse zero.
- Romans 4 whole-verse navigation divided at **4:9–16** and **4:17–22**, retaining both authorial streams; the historic fractional 17a/17b split is not representable as separate whole verses.
- 2 Chronicles 1 preface represented by a standard OSIS `div type="introduction"` and native chapter introduction; separate 1:1–12 section preserved.
- 31,098 numbered native K, 1,255 introduction I and two opaque TOP records. The full native archive has been built and independently read back.
- Representative real Xiphos passages and chapter-introduction behavior passed. Actual manual clicking of every reference is **not** certified; reader rendering remains an independent client concern.

## Authentic release payload

The [successful artifact review run](https://github.com/icfmp/Bible-Resources/actions/runs/44554276085) retained the exact final-`MHC` package with SHA-256 `c8d70166dd569674e936874cd9a94809bceb9642a76af7220ef86f2b71af93b2` (16,404,517 bytes), in immutable review artifact `14544781469`. Its seven exact compiled members are committed under `payload/`; the individual SHA-256s are recorded in `RELEASE_ARTIFACT_PROOF.json`. The official deterministic Pages/Release ZIP is recompressed from these unchanged same seven members and therefore has its **own** exact archive checksum, specified in the release plan.

**Native module collision:** upstream CrossWire already distributes a different `MHC` version **2.2**. This release intentionally uses the same SWORD module ID but Bible Resources version **0.1.0**. Installing it requires deliberate provider replacement; semantic version ordering must not be assumed to treat curated 0.1.0 as newer than upstream 2.2. Nothing is automatically uninstalled or migrated.

See [issue #285](https://github.com/icfmp/Bible-Resources/issues/285), merged [PR #286](https://github.com/icfmp/Bible-Resources/pull/286), and [PR #389](https://github.com/icfmp/Bible-Resources/pull/389). The source attestations are technical checks, not a claim of complete identity to every historical print witness.
