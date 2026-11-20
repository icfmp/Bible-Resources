# Source-first workspace layout

**Canonical convention (2026-11-20): resource type → ISO 639 language → stable resource ID.**
This convention applies to original and cleaned source data and new work,
independently of the compiled SWORD distribution layout.

## Real directory structure

```text
sources/
  original/
    bibles/
      fr/
        lsg-1910/fraLSG_usfm.zip
        lsg-1910/fraLSG_usfx.zip
        darby-jnd-2024/bible_jnd_2_0.xml
    commentaries/
      en/
        mhc-crosswire/mhc.osis.xml
  cleaned/
    bibles/fr/lsg-1910/lsg-1910.osis.xml
    bibles/fr/darby-jnd-2024/bible_jnd_2_0.osis.xml
    commentaries/en/mhc-crosswire/mhc.osis.xml
    commentaries/en/mhcc-crosswire/mhcc.osis.xml
    commentaries/en/hmcc-modern/hmcc-modern.osis.xml
    dictionaries/<language>/<resource-id>/
    encyclopedias/<language>/<resource-id>/
    other/<language>/<resource-id>/
work/
  <type>/<language>/<resource-id>/{drafts,audits,tests}/
modules/<resource-id>/                       # existing SWORD output; unchanged
scripts/                                     # stable current tool entrypoints
docs/evidence/                               # historic review, rights and receipts
```

The five categories, when populated, are `bibles`, `commentaries`,
`dictionaries`, `encyclopedias`, and `other`. Use **ISO 639-1** lowercase
two-letter language IDs (`fr`, `en`, `de`, etc.) when defined; for a
language without an ISO 639-1 code, use its registered ISO 639-3 identifier.
Do not invent language identifiers. Multiple independent curated editions in
the same language must have distinct stable resource IDs.

**Do not create empty category folders or README-only “source editions”.**
Git only needs the directories that contain actual original/cleaned source
bytes. Generic explanations belong here, not in fake editions. Existing
published SWORD binaries in `modules/` do not automatically imply that a
reproducible clean OSIS/USFM master is committed.

## Exact original sources

`sources/original/<type>/<language>/<resource-id>/` stores the **unchanged
actual original** (single OSIS, original USFM archive or approved source
container) only if exact-edition redistribution rights allow it. Retain a
resource-specific `PROVENANCE.json` recording edition/revision, official URL,
observed byte size and cryptographic SHA-256, license witness and identity of
the separately curated resource. An original PDF/ZIP/SWORD is not silently
renamed OSIS. Never strip whitespace or correct source markup here.

The initial real files in this tree are:
- Louis Segond 1910 original eBible **USFM ZIP** (French), SHA-256
  `64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900`
- BPC Darby **2024 rev. 2.0 OSIS XML** (French), SHA-256
  `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`
- CrossWire MHC version 2.2 **original authoring OSIS XML** (English), SHA-256
  `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`

These were independently SHA-verified against preexisting project manifests
before they were committed. They are **not** necessarily the exact uncommitted
cleaned-source revisions used to produce earlier releases.

## Reviewed cleaned sources

`sources/cleaned/<type>/<language>/<resource-id>/` stores the *actual* vetted
OSIS/USFM editorial source after structural cleanup and independent
source-faithfulness verification. A clean source is not just an original file
copied into a second directory. It needs source/cleaned hashes, approved
reversible rule-by-rule differences, standard structural checks, complete
annotation preservation and source-to-native SWORD round-trip evidence.

For Bibles, check words, punctuation, omissions, verse mapping, authorial notes,
cross-references, **all word-to-Strong/lemma/morphology associations**, and
translation-note anchors. For commentaries, check authorial commentary bodies,
paragraphs, introductions, section/range mapping and links. No manually edited
SWORD data is used as an invented source.

**Recovered and committed** approved editorial masters as of 2026-11-20:
- `sources/cleaned/bibles/fr/lsg-1910/lsg-1910.osis.xml`
  (version 0.1.0, exact source SHA `d6abd7416d026c86ce2e9577e3bfe7a10159c5c78d236913359c7fab013449d0`; historical u2o generator date
  2026-11-09 14:13:18 UTC established from original source SHA)
- `sources/cleaned/bibles/fr/darby-jnd-2024/bible_jnd_2_0.osis.xml`
  (version 0.1.1, exact source SHA `35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d`)
- `sources/cleaned/commentaries/en/mhc-crosswire/mhc.osis.xml`
  (version 0.1.0, exact source SHA `c64891f4fb2c3bd3a7e5e6cca992d80675849e7b3615f80ee95121461ef385f4`)
- `sources/cleaned/commentaries/en/mhcc-crosswire/mhcc.osis.xml`
  (classic MHCC 0.1.1, **new source reconstruction**, SHA `6aca55c36789f6f7d081b7cba2a167a8006cad9447ae8b50d619ad0de32dfb39`, all
  29,999 native indexed records—including 24 approved aliases—checked
  via SWORD round-trip; original historical authoring XML not recovered)
- `sources/cleaned/commentaries/en/hmcc-modern/hmcc-modern.osis.xml`
  (version 0.1.0, exact source SHA `23f0872a67086d9f659bd96936ab63db63c8c7b8c10eb92e59537c3e6cf16189`)

The historical MHC source-cleanup reports live under
[`docs/evidence/mhc-285/source-cleanup/`](evidence/mhc-285/source-cleanup/),
not inside the clean source folder. The original historical CrossWire **MHCC authoring OSIS** has not been
recovered. The classic 0.1.1 OSIS stored here is an independently validated
**derivative reconstruction**, not a false claim of byte-exact authoring identity. Always distinguish a new
equivalent-looking output from a byte-exact restored authoring source.

## Work, documentation, release outputs and compatibility

Use `work/<type>/<language>/<resource-id>/` for **new** temporary drafts,
audits and nonauthoritative tests; only commit durable, rights-cleared evidence.
The preexisting 1,332 HMCC Modern manuscripts under `work/mhcc-modern/`
remain at their historical locations so previous source-bound GitHub links,
hash references and active build scripts remain valid. Likewise, the already
moved MHC CCEL experiment is a historical exception at
`work/commentaries/mhc-crosswire/experiments/ccel-imp/`. Do not treat
these existing legacy paths as templates for new work.

The `modules/<resource-id>/payload/` native SWORD paths, release identity,
release plans, catalogue, signed editorial records and actual published packages
must **never** be mass-relocated with editorial source organization changes.
Releases remain reproducible from their explicitly approved source/proof
contracts; file movements alone are not permission to republish.

Script cleanup is a **different** audited task [#430](https://github.com/icfmp/Bible-Resources/issues/430).
The existing [tool registry](TOOL_REGISTRY.md) notes 177 script entrypoints
with real references; archive/merge only once tests, workflows, Python imports,
historical tags and shared behavior have been checked.

## New-source acceptance gates

1. Identify source edition, actual standard format and legal permissions.
2. Pin the **original byte source** in the proper type/language directory.
3. Build the cleaned candidate independently without touching the original.
4. Validate standard structural markup and full-corpus fidelity, including
   annotations, translated word alignment and exact source references.
5. Compile standard SWORD from the reviewed cleaned master and independently
   read back native content and reference navigation in diatheke/Xiphos.
6. Keep immutable proofs, seek the mandatory editorial/rights approvals,
   and publish via the existing GitHub Release-before-Pages process.

See [source-first pipeline](SOURCE_FIRST_EDITORIAL_PIPELINE.md),
[normalization](NORMALIZATION_POLICY.md), [editorial rules](EDITORIAL_RULES.md)
and [publishing](PUBLISHING.md).
