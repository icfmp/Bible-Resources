# Source availability by type and language

The source store has **actual original files**, not placeholder editions.
The three original bodies were imported on 2026-11-20 from their pinned
sources and independently checked against the existing audit digests. The
Segond original USFX witness archive was added during exact OSIS recovery.
A downloaded original and a reviewed cleaned master are **different stages**.
The published SWORD packages remain in `modules/<id>/`. Exact cleaned-source
hashes and independent historical production proofs are in each cleaned
resource's `CLEANUP_MANIFEST.json`; these are version-specific editorial
masters, **not newly edited commentary prose**.

| Type | Language | Resource | Original actually committed | Cleaned OSIS/USFM master committed? |
| --- | --- | --- | --- | --- |
| Bible | fr | [Louis Segond 1910](../../modules/lsg-1910/metadata.json) | [USFM archive](../../sources/original/bibles/fr/lsg-1910/fraLSG_usfm.zip) · [provenance](../../sources/original/bibles/fr/lsg-1910/PROVENANCE.json) | **Yes** — [verified 0.1.0 OSIS](../../sources/cleaned/bibles/fr/lsg-1910/lsg-1910.osis.xml), SHA-256 `d6abd741…` |
| Bible | fr | [Darby 2024](../../modules/darby-jnd-2024/metadata.json) | [OSIS XML](../../sources/original/bibles/fr/darby-jnd-2024/bible_jnd_2_0.xml) · [provenance](../../sources/original/bibles/fr/darby-jnd-2024/PROVENANCE.json) | **Yes** — [verified 0.1.1 OSIS](../../sources/cleaned/bibles/fr/darby-jnd-2024/bible_jnd_2_0.osis.xml), SHA-256 `35eb23c6…` |
| Commentary | en | [Matthew Henry Complete](../../modules/mhc-crosswire/metadata.json) | [authoring OSIS XML](../../sources/original/commentaries/en/mhc-crosswire/mhc.osis.xml) · [provenance](../../sources/original/commentaries/en/mhc-crosswire/PROVENANCE.json) | **Yes** — [verified 0.1.0 OSIS](../../sources/cleaned/commentaries/en/mhc-crosswire/mhc.osis.xml), SHA-256 `c64891f4…` |
| Commentary | en | [Matthew Henry Concise](../../modules/mhcc-crosswire/metadata.json) | Source witness identified in the official module/release records; **no original authoring OSIS file committed** | **Yes — rebuilt, not the historic source** — [OSIS for classic MHCC 0.1.1](../../sources/cleaned/commentaries/en/mhcc-crosswire/mhcc.osis.xml), SHA-256 `6aca55c3…`; recompilation verified against the complete published native corpus |
| Commentary | en | [Henry's Modern Concise Commentary](../../modules/hmcc-modern/metadata.json) | Distinct modern edition, licensing and editorial evidence documented with [historical manuscripts](../../work/commentaries/hmcc-modern/README.md) | **Yes** — [verified 0.1.0 OSIS](../../sources/cleaned/commentaries/en/hmcc-modern/hmcc-modern.osis.xml), SHA-256 `23f0872a…` |

Other types — dictionaries, encyclopedias, etc. — are only created in the
source tree when actual licensed source files are obtained. The independent
`entity-index/` project data does not automatically constitute an original
encyclopedia/dictionary text.

## Recovery status and limits

The four original-format editorial compiler inputs were recovered by replaying
historical source transformations and matching existing source SHA-256 identities.
The fifth, **MHCC classic**, was reconstructed as a **new OSIS editorial
source derivative** from its existing authoritatively released 0.1.1 native
SWORD. All 28,742 numbered, 1,255 introduction and two opaque TOP entries
were independently checked through an isolated OSIS→SWORD recompile for
unchanged words, punctuation, ordered references, semantic markup and
section aliases. The OSIS was not recovered byte-for-byte from an upstream
CrossWire authoring XML, and is never described as such. No original Bible text, commentary prose or SWORD
release was changed. LSG 1910 is recovered to byte-identical approved 0.1.0 source input;
its original converter-inserted timestamp (2026-11-09 14:13:18 UTC) was
independently found from the historical source SHA without changing any verse.
The original historical CrossWire MHCC authoring OSIS, if one existed,
remains unavailable; our reconstructed, version-specific MHCC source is
**not** an upstream original.

## Other working material

- [Historical MHC original-to-cleaned source receipts](../../sources/cleaned/commentaries/en/mhc-crosswire/editorial/evidence/source-cleanup)
- [HMCC Modern working manuscript index](../../work/commentaries/hmcc-modern/README.md):
  source-bound originals and review history remain under `work/mhcc-modern/`
- [Historical CCEL private experiment](../../work/commentaries/mhc-crosswire/experiments/ccel-imp/README.md)
- [Script lifecycle consolidation #430](https://github.com/icfmp/Bible-Resources/issues/430)

The canonical workflow and directory rules are in
[WORKSPACE_LAYOUT.md](../../docs/architecture/WORKSPACE_LAYOUT.md) and
[SOURCE_FIRST_EDITORIAL_PIPELINE.md](../../docs/workflows/SOURCE_FIRST_EDITORIAL_PIPELINE.md).
