# MHCC Modern English — whole-canon published-native XML census and introduction ownership

**18 November 2026 — primary original source metadata verified, modern derivative still NOT editorially accepted.**

## Source and reproducibility

This is an analysis of the **existing original-SWORD metadata artifact**, not a second interpretation or exported original authorial text. The authenticated full-canon receipt was generated with real libSWORD from the **published corrected `MHCC 0.1.1` release**. The [successful CI run #44270683938](https://github.com/icfmp/Bible-Resources/actions/runs/44270683938) contains the metadata-only artifact `mhcc-modern-0.1.1-source-native-receipt` and its `mhcc-modern-whole-canon-native-receipt.json` member. The exact source ZIP SHA-256 is `a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746`; full ordered raw native corpus SHA-256 is `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`.

All counts below traverse each chapter's **distinct original K raw body once**, not every aliased K verse address. Counting aliases as separate authored bodies would dramatically inflate the result. Source identity is verified by the original whole-corpus SHA; no XML, prose, or reference-target literals are reproduced here.

## Exact recorded source-markup census

| Source-native property | Observed result |
| --- | ---: |
| Canonical chapters | **1,189** |
| Chapters with numbered original K authored bodies | **1,187** |
| Distinct numbered K raw authorial bodies | **4,047** |
| Original numbered K addresses | **28,742** |
| Strictly XML-parseable distinct original K raw bodies | **4,047 / 4,047** |
| Original `<reference>` elements across distinct K bodies | **1,204** |
| Distinct K bodies containing a reference element | **669** |
| Chapters containing an original K reference element | **535** |
| Original `<table>` elements in distinct K bodies | **2,531** |
| Distinct K bodies containing tables | **792** |
| Original `<title>` elements in distinct K bodies | **2,046** |
| Original `<note>` elements in distinct K bodies | **0** |
| Original `<p>` elements in distinct K bodies | **0** |

**Interpretation limits:** these are counts of the listed literal XML tags, not a claim that the source has no note-like explanations, paragraphs or typographic breaks represented in some other way. Zero `<p>` tags is emphatically **not** permission to ignore authorial divisions or to treat new Markdown blank lines as source paragraphs. The 1,204 reference *elements* are not a count of unique destination verses. None of these counts demonstrates that equivalent original targets, markup or semantics have been transferred into the modern derivative.

### Reference-rich books: first practical audit priority

| Original book | Native reference elements |
| --- | ---: |
| Isaiah | 186 |
| Jeremiah | 148 |
| Genesis | 110 |
| Ezekiel | 98 |
| Exodus | 89 |
| Matthew | 53 |
| Numbers | 47 |
| Daniel | 39 |
| Job | 35 |
| Psalms | 35 |

Highest individually linked original bodies for focused preservation testing include: `Exod.12.1–20` (**13** reference elements), `Ezek.8.1–6` (**8**), `Exod.14.21–31` (**7**), `Exod.29.1–37` (**7**), and `Gen.3.6–8` (**5**). These scopes come from the original native receipt; no conclusion about missing modern links can be drawn merely from their original counts.

## One noncontiguous native K body — Matthew 13

The same whole-canon SHA-pinned source-group inventory identified **one** source body whose original occupied K addresses form disjoint runs: `Matt.13.24–30` **and** `Matt.13.36–43` (15 addresses), with one authored original body. **`Matt.13.31–35` belongs to a separate original raw K body** (five addresses). This is a source-key topology property, **not** an invitation to write or reassign text. The modern manuscript `accepted/matthew-13.md` already expresses these two disjoint runs in one heading and separately covers 31–35. No new textual correction is warranted.

The generic metadata-to-modern draft guard must validate the **exact occupied verse-key set**, not merely the first and last key. In particular, it must reject an apparently convenient `Matt.13.24–43` continuous range because that would shadow the genuine intervening commentary body. A regression test now covers correct and invalid noncontiguous headings; the temporary OSIS `annotateRef` serialization is also tested for two separated groups. The already established five source-to-modern **topology mismatch** cases remain a different category; this Matthew 13 topology is present and correctly represented in the draft.

## Proven actual introduction ownership (the original I namespace is not uniform)

The same authenticated receipt records twelve nonempty I addresses, whose content **types are not equivalent**:

| Original source address | What the native structure supports | Original visible words | Raw SHA-256 |
| --- | --- | ---: | --- |
| `I:2John.1` | Introduction prose | 71 | `66b0ff85b9755dd658d202b223ce2d6f2c80a568cde6a4f8e1a7c98f33686ced` |
| `I:3John.1` | Introduction prose | 27 | `8dac353b7cc7a8bfff92570c5a62568c1bbbc94f678dabf8fda8f4001e15c137` |
| `I:Jude.1` | Introduction prose | 106 | `c902ee756da07650151934670414f8d1f633febc4843c54f22e33a022bf639cd` |
| `I:Obad.1` | Introduction prose | 32 | `8ad0ed081f3bc24169b28e2b1246f04cd515be411c0ffffa381b6ec8087771cf` |
| `I:Phlm.1` | Introduction prose | 117 | `9cf0b2ee7e0e73762d096520fe71d62c7c3f3ec9475e4d33a1ffe6806b527fcc` |
| `I:Lev.19` | Entire chapter exposition, **no original K bodies** | 698 | `de49e95300a947014836f46997124d9b3e0a1b21d7bc0788dcc6da825958c6ec` |
| `I:Ps.108` | Entire chapter exposition, **no original K bodies** | 136 | `596b643eb9807198a002855783abe1981e09d4b254a7aa801c0085ab0e969375` |

The remaining five nonempty I records are short book-title entries `I:2John` (2 words), `I:3John` (2), `I:Jude` (1), `I:Obad` (1), `I:Phlm` (1), **not alternate copies of the five full introductions**. This source structure is different again from Genesis 1, where the book introduction is embedded in the first numbered K body despite two original I placeholders with no visible authorial prose.

Five existing modern **introduction candidates** now record their exact published-source *chapter-I* key and raw SHA. Their translated clauses and original native formatting still require separate human/independent comparison; *source location attested* does not mean *modern candidate approved*. No duplicate book-I or K body may be generated for those five chapters. The two I-only whole-chapter cases, Lev.19 and Ps.108, retain the separately agreed narrow 37/13 verse-linked future-derivative treatment, not a general chapter fallback.

## Next release gates, kept strictly separate

1. Build **source-native link-identity and ordering expectations** for all 1,204 `<reference>` elements (not only their counts), trace them to the corresponding modern authorial units and verify the actual generated `osisRef` values after private compilation and native readback. Existing Genesis 1 exact-reference preservation (two original links) is **only a pilot**.
2. Compare original title/table/division markup and all I entries against explicitly chosen modern presentation. Never infer original `<p>` structure from absent tags or Markdown layout.
3. Independently assess each modern statement against the exact compiled original and label secondary-source-only restorations separately (especially `1Sam.25`, `Ps.95`).
4. Only after full editorial approval, source rights and actual reader QA should a separate modern SWORD edition be considered for owner-authorized publication.

**Original published MHCC 0.1.1, native keys and binary data were not changed. No modern SWORD module assembled or published; PR #272 remains draft, 0/1,189 independently signed off.**
