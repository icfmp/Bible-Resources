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

## Original Bible-link identity ledger (source-only, NOT modern link transfer)

The pre-existing generic `commentary_modern_reference_gate.py` now also supports an authenticated **whole-canon original-only audit**. It uses the exact, released real SWORD raw-stream reader and complete 1,189-chapter receipt to check the SHA of **every original occupied numbered K address**, not merely first/last samples. Each of the original 4,047 K authorial bodies is independently reconciled to its signed source SHA; every original XML `<reference osisRef="…">…</reference>` in those bodies is visited in its authored document order.

The resulting **metadata-only** receipt lists each link-bearing source body's first/last original K addresses, source raw SHA and the **ordered SHA-256 fingerprints of the original literal `osisRef` target and original visible link label**. This records duplicate occurrences and exact source literal identity without publishing original target literals, link labels, prose or XML. It deliberately **does not canonicalize** source targets to its own guessed verse syntax: legitimate multi-verse or unconventional original links must not be silently rewritten. A missing or unsafe `osisRef`, unexpected K alias, changed source body, wrong link count, duplicated source key or incomplete corpus is blocking.

The original-native CI step **PASSED** on [run #44276719759](https://github.com/icfmp/Bible-Resources/actions/runs/44276719759), confirming **1,204 original `<reference>` occurrences across 669 distinct numbered-K bodies**, **4,047 original authored K bodies** and **28,742 original numbered addresses**. Its new metadata-only report is `mhcc-modern-all-original-link-identity-sha.json` in the existing CI artifact.

**Multiplicity audit of the exact hashed original source:** these 1,204 occurrences belong to **535 chapters in 54 books**; **368** original K bodies have one hyperlink, while **301** have multiple. No linked display label is empty. In `Exod.12.1`, the source has **13 link elements but only 12 distinct targets**, including two occurrences with the *same target and label*. This is source evidence, not an automatic approval to simplify it: the modern edition must not silently deduplicate the two source occurrences. A generic synthetic regression protects this invariant.

**Crucial distinction:** This is a reversible *source inventory*, not a cross-language linker. It **does not prove** that any of the 1,204 links appear in the modern manuscripts, are positioned at the correct translated phrase or survive a compiled modern SWORD roundtrip. The existing Genesis 1 source-linked pilot tests only **two** known links. The next separate editorial/technical task is to map these 669 link-bearing authorial bodies to their exact modern sections, approve marker text and placement, then compare generated original literal `osisRef` identities and occurrence order with the new ledger during real private compiled readback.

## Distinguish original link identity from a correct modern-derivative target

**2026-11-18 bounded editorial exception discovery:** the source-original 1,204 links are an **unaltered evidence baseline, not 1,204 automatically authoritative destinations for the derived edition**. In [Genesis 2–3 / Exodus 12](GENESIS_EXODUS_NATIVE_REFERENCE_DISPOSITIONS_2026-11-18.md), eleven original compiled links are demonstrably suspect across seven Genesis/Exodus chapters: six prose list-item numbers accidentally linked as Scripture and five genuine abbreviated verses linked to the wrong biblical book, including **Hebrews 2:14** misdirected to **2 Corinthians 2:14**. Revelation 22:2 is cited in Genesis 2's authored prose but does not have its proper original hyperlink. A single-digit source link label cannot safely be suppressed by rule, because **1 Corinthians 5:8** in Exodus 12 uses a genuinely abbreviated `8` label.

Those cases are recorded separately, with original literal target and display-label **hashes/occurrence ordinals**, precise authorial-group raw SHA-256, modern manuscript section and evidence from the secondary source witness. The matching [bounded machine-readable proposal](GENESIS_EXODUS_REFERENCE_DISPOSITIONS.json) is an explicit editorial exception ledger. The [30 one-digit source-label candidates](ORIGINAL_SINGLE_DIGIT_LINK_TRIAGE_2026-11-18.md) are separately screened: 6 confirmed spurious numbers, 4 confirmed wrong-book links, 3 legitimate one-digit cross-references, **17 awaiting witness review**. Never equate a one-digit linked label with a wrong reference without checking its context. It does **not** mutate the original, authorize changes to other source elements, or constitute a compiled/verified derivative. Future link compilation must distinguish **exact-copy decisions**, **documented corrections**, **additions supported by the source's prose**, and **quarantined unresolved references**.

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
