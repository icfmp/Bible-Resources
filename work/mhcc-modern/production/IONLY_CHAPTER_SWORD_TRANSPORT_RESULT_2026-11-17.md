# Modern MHCC — isolated I-only chapter link transport proof (2026-11-17)

**Result: PASS — native technical SWORD transport only.** Do **not** interpret
this as editorial approval, whole-edition compilation, reader compatibility
signoff, publication permission, or a general chapter-wide fallback policy.

- Draft PR: [#272](https://github.com/icfmp/Bible-Resources/pull/272).
- Exactly pinned original: publicly released `MHCC` **0.1.1**, ZIP
  SHA-256 `a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746`;
  complete source corpus SHA-256
  `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`.
- Independent full native inventory and whole-canon receipt: 1,189 canonical
  chapter manuscripts inventoried, 28,742 original occupied numbered K slots,
  4,047 distinct original numbered raw K groups, and two observed I-only
  original commentary chapters.
- Test workflow: [Actions #44186352658](https://github.com/icfmp/Bible-Resources/actions/runs/44186352658)
  **SUCCESS**; all steps including actual compilation and linked readback passed.
  Existing source receipt synthetic suite: **34 tests PASS**.

## Exactly two tested source chapters

| Chapter | Authoritative original source owner | Original numbered commentary keys | Independently pinned I SHA-256 | New private preview K keys | Native adjacent `isLinked` pairs |
| --- | --- | ---: | --- | ---: | ---: |
| `Lev.19` | Chapter I, 698 visible source word tokens | 0 | `de49e95300a947014836f46997124d9b3e0a1b21d7bc0788dcc6da825958c6ec` | 37 (verses 1–37) | 36/36 |
| `Ps.108` | Chapter I, 136 visible source word tokens | 0 | `596b643eb9807198a002855783abe1981e09d4b254a7aa801c0085ab0e969375` | 13 (verses 1–13) | 12/12 |

The pinned I records contain no original `reference` or `note`
elements. Original-native I ownership and byte hashes are verified against the
full 0.1.1 raw corpus, not guessed from CCEL or verse headings.

## Reproduction

The explicitly scoped manifest
[`IONLY_CHAPTER_LINK_PREVIEW.json`](IONLY_CHAPTER_LINK_PREVIEW.json)
names both chapters, 37/13 verse bounds, original I SHA-256 evidence, and
the exact unshipped Modern English chapter manuscripts.
[`scripts/commentary_modern_ionly_preview.py`](../../../scripts/commentary_modern_ionly_preview.py)
refuses to act if the compiled source has any original numbered K commentary
in either chapter. It emits one annotated OSIS section
(`Lev.19.1-Lev.19.37` or `Ps.108.1-Ps.108.13`) per chapter. It does not
alter published MHCC or materialize one copied text per verse.

The CI workflow independently:

1. Checks the exact source ZIP/corpus identity; streams the complete original
   native corpus and verifies both I-only owners against the manifest.
2. Produces a **temporary** OSIS document from the current separate Modern
   English chapter drafts and compiles a **temporary** `zCom` using stock
   `osis2mod` (`Versification=KJV`, `BlockType=CHAPTER`).
3. Queries the **actual native KJV registry**: the specified chapters really
   have 37 and 13 verses.
4. Reads the temporary module's **50 exact K records**: every declared verse
   has a record; within each chapter all raw records share the same byte hash.
5. Uses the standard `SWModule::isLinked` inspector, **not raw-byte equality
   as a proxy for a link**: all 48 adjacent pairs are truly native-linked,
   no independent per-verse duplicates or unlinked intervening keys.
6. Checks that the modern chapter body is not also duplicated at chapter I,
   and checks first/last verse display through the independent `diatheke`
   command-line reader. The result is
   `I_ONLY_SWORD_NATIVE_LINK_PASS chapters=2 linked_verse_keys=50 adjacent_isLinked_pairs=48 independent_authorial_sections=2`.

The workflow uploads metadata **only**; it neither uploads the temporary
compiled module nor ships any original/source text as an artifact.

## Explicit non-goals and remaining gates

- **No general chapter-commentary fallback rule.** A whole-chapter authorial
  introduction elsewhere must be left for the reader to present appropriately.
  Never fill unannotated verse gaps in chapters with verse-specific commentary.
- The two accepted Markdown files are *production translation candidates*,
  not signed-off source-native translations. Original I headings, exact source
  meaning/doctrinal nuance, and all original markup structures still require
  detailed independent editorial collation. The `laws.` source-title
  witness in Leviticus is **not independently native-title accepted**.
- This proves stock SWORD's transport and `diatheke` basic readback, not
  Xiphos GUI, AndBible/JSword, Bible application scroll sync, or publication
  in the original resource catalogue.
- The full 1,189-chapter derivative still needs its own verified source
  section mapping, build/readback, and genuine editorial and rights approvals.
- Original released `MHCC` 0.1.1 remains unchanged; no merge/publication
  is authorized.

**Outcome:** the narrowly requested transport can be implemented using
one authored commentary per chapter with genuine native K aliases, without
inventing original verse divisions or a global application display rule.
