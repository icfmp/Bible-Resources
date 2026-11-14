# MHCC — original native section-scope editorial audit, checkpoint 1

**Date:** 2026-11-14. **Tracker:** [#274](https://github.com/icfmp/Bible-Resources/issues/274). **Tool:** draft [PR #275](https://github.com/icfmp/Bible-Resources/pull/275).

**Status:** Exact-stock native entry/range pass **completed**, independently witnessed section-reference pass **completed**, wider editorial/content/intro review **NOT completed**. **No corrections, release or modern-English chapter approvals**. Do not use this checkpoint as an edition-wide editorial PASS.

## Exact digital inputs

| Witness | Identity |
| --- | --- |
| CrossWire original `MHCC` 2.0 ZIP | SHA-256 `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d` |
| Original full unfiltered compiled native key/raw stream | SHA-256 `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6` |
| Independent CCEL ThML XML (NOT assumed same edition) | SHA-256 `4a5509ba5064b54572397ae1a796561ff6ce4a1e18f366af0141a09c5d06fcd6` |
| Published BRMHCC 0.1.0 ZIP (unchanged) | SHA-256 `0faf4376b6b97093ecb94f306886c24d3030ab1f5e194472ad908dd73921f9c0` |

Reproduction and outputs:
- [Native audit and range probes — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43604048677)
- [Full 16 original native defects listed — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43604225054)
- [Pinned CCEL source and stock heading comparison — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43604416806)
- [Exact source `scripRef` values for all 16 — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43604818118)
- [Source `scripCom` / `scripRef` concordance matrix — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43605317714)
- [Five independently unmatched section starts — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43605465103)

The read-only generic tool uses complete private libSWORD raw-entry framing, a *separate* indexed-key read, and both independently pinned sources. Original prose/XML are never emitted into logs or artifacts. The result JSON is temporary metadata only. The parser deliberately treats section headings as candidates, not as a licensed instruction to modify indexing.

## Exact native scan and detected grouping

- All **29,975** occupied original keys read and SHA-attested (28,718 numbered, 1,255 introduction, 2 TOP).
- **3,927** start-anchored numbered section headings inferred from the original compiled module.
- **3,443** explicit dash-ranges: all declared native verse slots occupied with identical raw SWORD payloads.
- **468** single-verse headings.
- **16** comma-enumerated verse sections: all lack their second numbered SWORD index key, although the original commentary section starts at the first key and declares both verses. **The entire original prose was not proved missing.**
- **140** original numbered slot rows have no recognized leading heading, so the simple heuristic provides no range verdict. These require a separate audit, not a `PASS`.

### Sixteen repeated index omissions in CrossWire 2.0

| Authored section scope observed in stock | Absent original numbered SWORD key |
| --- | --- |
| Eccl 4:7–8 | `Eccl.4.8` |
| Eccl 9:11–12 | `Eccl.9.12` |
| Song 1:7–8 | `Song.1.8` |
| Song 6:2–3 | `Song.6.3` |
| Song 8:13–14 | `Song.8.14` |
| Isa 21:11–12 | `Isa.21.12` |
| Isa 26:20–21 | `Isa.26.21` |
| Isa 50:10–11 | `Isa.50.11` |
| Isa 56:1–2 | `Isa.56.2` |
| Isa 57:1–2 | `Isa.57.2` |
| Isa 58:1–2 | `Isa.58.2` |
| Isa 58:13–14 | `Isa.58.14` |
| Isa 61:10–11 | `Isa.61.11` |
| Jer 4:1–2 | `Jer.4.2` |
| Jer 4:3–4 | `Jer.4.4` |
| Lam 4:21–22 | `Lam.4.22` |

Each corresponding **independent CCEL XML** shows the complete correct passage range in at least one original `scripRef osisRef` citation. Example: `Bible:Song.1.7-Song.1.8`. The same 16 do **not** match exact original `scripCom` section anchors. This is strong independent evidence of intended section scope, *not* proof of which converter implementation introduced the missing SWORD key. A citation is not interchangeable with a commentary annotation anchor.

## Cross-edition source-reference concordance

Across all 3,927 stock start-anchored headings:

| Independent exact-scope evidence | Count |
| --- | ---: |
| Both CCEL `scripCom` and `scripRef` | 3,237 |
| Only `scripCom` | 119 |
| Only `scripRef` | 566 |
| Neither | **5** |
| **Total** | **3,927** |

The five *neither* starts are **Jude 1:1–4; 1:5–7; 1:8–16; 1:17–23; 1:24–25**. Crucially, these coincide with the already-documented **CCEL Jude-vs-Judges `scripCom` book-code conflict**, not five newly proven CrossWire content gaps. See [prior exact source metadata evidence](../mhcc-177/one-original-title-jude-vs-judg-osis-conflict.json) and the [five-case research queue](../mhcc-177/source-book-identity-five-case-review-queue.md). The original conflicting CCEL book codes are not silently modified. A title/book alias explains the mismatch as a hypothesis with existing documented independent evidence, not a correction authorization.

These are **reference-scope signals only**, and the same CCEL XML is a different digital edition. They do not prove semantic, punctuation, notes, paragraphs or historical print equivalence. In particular, a `scripRef` can be a cross-reference rather than a `scripCom` section marker.

## Editorial conclusion and remaining acceptance gates

**Confirmed:** the publicly reused upstream stock has 16 repeated native verse-index coverage omissions for comma-enumerated section headings. The curated BRMHCC retains these because it intentionally copies upstream compressed payload bytes.

**Not confirmed:** authored prose lost at those verses; that the original author or print editor made the mistake; the CrossWire converter's precise fault; equivalence between CCEL XML, CrossWire compiled text and Moody print; completeness of all introductions/cross-references/poetry/quotation placement; semantic text integrity beyond the existing source-identity limited checks.

**Required before a corrected edition:**
1. Review the exact 16 source section boundaries and the 140 unclassified native rows independently; examine real context and all book/chapter introductions.
2. Validate actual scripture link destinations, chapter summaries and source-versus-compiled prose differences, including the known five same-book CCEL/CrossWire lexical review cases from [the previous research queue](../mhcc-177/source-book-identity-five-case-review-queue.md).
3. Choose and review a **reversible native indexing strategy** that preserves original commentary XML, authorial text and all existing occupied keys; add only independently justified coverages and make it work for generic commentaries, not these hardcoded keys.
4. Build a separate candidate and prove exact original 29,975-key raw equality, expected **additional** addressable keys, correct linked text on each, stable verse boundary behavior, and full preserved intros/refs. Test in one authentic independent reader; no unbounded client matrix.
5. Propose upstream CrossWire/CCEL corrections with evidence, and seek explicit owner approval before any publication. Never silently overwrite original BRMHCC 0.1.0 or resume the paused modern-English edition #270.

**Every published original and independent witness remains unchanged.**


## Second pass — unlabelled chapters and discontinuous ranges (2026-11-14)

**This section supersedes the 3,927-section / 140-unknown / 16-index-case preliminary
figures above; earlier results remain as dated reproducible checkpoints.**

Exact original SHA-pinned stock scan and independent CCEL comparison
[Actions #43609634615](https://github.com/icfmp/Bible-Resources/actions/runs/43609634615)
**PASS**; 19 synthetic tests **PASS**.

- **3,928** distinct start-anchored section headings identified (previously 3,927).
- **3,443** continuous dash groups, **468** single-verse groups, **16** comma groups and **one discontinuous multi-range group**.
- **17** original native index coverage failures across explicitly declared section headings, corresponding to **24 missing numbered SWORD slots**: the previously documented 16 two-verse groups plus the eight verse continuation slots in **Matthew 13:36–43**.
- Matthew 13:24–30 **and 36–43** form one authorial exposition of the parable of the tares. The *same stock payload* is occupied in Matt 13:24–30, whereas **all eight keys 13:36–43 are unoccupied**. Different publisher-independent displays agree on the unusual discontiguous scope: [Biblia](https://biblia.com/books/mhenryc/Mt13.1-23), [Christianity.com](https://www.christianity.com/bible/commentary/matthew-henry-concise/matthew/13), and [a preserved alternative transcription](https://sacred-texts.com/bib/cmt/mhcc/mat013.htm). These witnesses establish a source-reading hypothesis, not identical edition provenance.
- **133** native numbered rows lack a recognized *simple* number heading after recognizing Matthew's discontiguous reference: 131 with nonnumeric XML title and 2 with unparsed mention of the word “Verse”. They are **119 distinct raw source payloads**.
- **119** of the 133 unrecognized rows occur at a chapter's **first verse**; the remaining **14** are Amos 1:2–15 repeating exactly the same raw text as Amos 1:1.
- **118** of the 119 chapter-first rows are the **only occupied native SWORD verse-key in their entire chapter**. The single exception is Amos 1, whose identical whole-chapter raw text is available at 15 individual native keys. This is a **chapter-level coverage design / editorial scope question**, not proof of lost words.
- In the independent *different-edition* CCEL ThML, **none of the 119 distinct unrecognized original stock payloads** corresponds to a strictly parseable explicit multi-verse `scripCom` annotation beginning at the same native key. The parser found one such annotated multi-verse group for Matt 13:24–30 only; its second range 36–43 is not in a continuous simple `scripCom` endpoint.
- The strict *independent* agreement matrix for 3,928 starts is now 3,237 `scripCom`+`scripRef`, 119 `scripCom` only, 566 `scripRef` only and **6 neither**. The additional “neither” is Matthew 13's **noncontiguous** section; five previously known Jude/Judges source-bookcode conflicts remain distinct. These six are **not automatically source errors**.

**Interpretive boundary:** A chapter with exactly one original stock SWORD verse slot can intentionally be represented by a single chapter-level comment anchored to verse 1. It may be inconvenient for verse-based reading, but one cannot silently duplicate that comment to all verses and call it a *textual correction*. The corresponding original chapter body, author's scope and source editorial conventions must be verified before considering a navigational enrichment.

**Remaining gates:** (1) inspect chapter divisions with no `scripCom` unit and determine whether every “chapter-level” comment genuinely covers the whole chapter; (2) classify the two Psalms with a non-heading verse mention without changing prose; (3) verify original source-to-compiled text fidelity, references, headings, intros and 17 confirmed indexing cases; (4) prepare a generic, reversible index patch proposal separately with explicit editorial review and owner authorization. **No source bytes or published assets changed.**


### Sampled editorial interpretation and future correction safeguards

A separate English concise edition displays **Genesis 36 as a single whole-chapter exposition**, without an authored verse-range subheading: [Christianity.com concise Genesis 36](https://www.christianity.com/bible/commentary/matthew-henry-concise/genesis/36) and [UECF Genesis 36, 1 section](https://www.uecf.net/matthew-henry-commentary/genesis/36). That is consistent with the only occupied native stock key `Gen.36.1`, although it does not establish the intended SWORD per-verse access for the other verses, nor independently certify all 118 chapters. **Do not classify all 118 chapter-first entries as text/verse-index corruption simply because the source has one chapter-level section.**

For Matthew 13, the two **discontinuous** ranges must remain separate: `24–30` and `36–43`. Verses `31–35` have their **own** commentary. A repair that blindly fills the continuous range `24–43` would overwrite or misattribute a genuine independent section and is **forbidden**. The generic correction proposal must support disjoint ranges and must fail closed on already occupied keys.

Before treating unlabelled whole-chapter prose as needing any additional verse links, require a separately grounded chapter-scope decision (source division, per-chapter citation or independently corroborated edition presentation), verify actual KJV chapter bounds and that no occupied key is overwritten, then record an explicit reversibility receipt. This is a different class of decision from a missing continuation whose *authorial heading already names the exact verses*.


## Third pass — exact native chapter bounds and all source chapter wrappers (2026-11-14)

This checkpoint supersedes earlier *scope-coverage* limitations but does **not** approve a modified edition.

- [SWORD original full native versification run #43615759574](https://github.com/icfmp/Bible-Resources/actions/runs/43615759574) **PASS**: the independent released libSWORD verse registry reports exactly **1,189 KJV chapters / 31,102 canonical verse locations**; all 28,718 existing numbered stock commentary slots are inside that registry. No canonical verse is inferred from the highest occupied commentary key. The proposed generic navigation planner cannot target an unavailable verse.
- The **118** candidate chapters with only one occupied original `zCom` key at verse 1 could gain **2,285 additional verse-navigation aliases** *if* all were independently determined to be whole-chapter sections. **This is a maximum potential based on valid native chapter boundaries, not 2,285 approved alterations.**
- [CCEL independent chapter marker run #43615364865](https://github.com/icfmp/Bible-Resources/actions/runs/43615364865) **PASS**: 228 original ThML chapter-form `scripCom` markers; **20** of the 118 stock single-key chapters have one independent nonempty chapter-level marker and no additional verse/range `scripCom` in that `div2`. The other **98** lack that exact chapter marker — not proof that their text is verse-one-only.
- [Whole original source `div2` structure run #43616351935](https://github.com/icfmp/Bible-Resources/actions/runs/43616351935) **PASS**: one extra original `div1` containing `div2` elements is a **non-Bible index/appendix**, evidenced separately in [the pre-existing 68-divisions inventory](../mhcc-177/all-unmarked-original-div1-structural-coverage.json). We excluded this unassignable source division from canonical book mapping without dropping its content or assigning its pages to biblical chapters.
- After conservative canonical book-title/source-reference comparison and *exact* source/natively enumerated chapter counts, **96 / 118** stock one-key chapters have independently corroborating `div2` units containing text, with no explicit nested verse-scope `scripCom` sections. They are **source-structure whole-chapter candidates**, not yet authorial text parity or an editor-reviewed corrected key list.
- **22 / 118** unresolved chapter candidates are **all in 2 Chronicles**. This is a demonstrably unsafe source-book / source-chapter alignment region: source book identity and/or numbered chapter count differs, and some mapped source `div2` have verse-range annotations. We therefore do **not** automatically associate original `div2` ordinals with native `2Chr` chapter references, even when a plausible sequence appears. A separate source-headings and actual-annotation review is mandatory.
- Across all 66 KJV books, the *source book mapping evidence* classifies 60 with matching title and book-code markers; one original book-code conflict, three title alias ambiguities, and two chapter count discrepancies. These classifications are **not** 6 newly found corruptions and do not override the original XML's conflicting titles or reference attributes.

The new reusable checks are in `scripts/commentary_section_scope_audit.py` (full original privately parsed ThML versus native stock and reference fingerprints), `scripts/sword_native_commentary_index.cpp --chapter-registry` (actual released SWORD verse limits), and `scripts/commentary_navigation_link_plan.py` (read-only reviewed-scope alias proposal).

**Acceptance gates before any corrected SWORD candidate:** (1) finish the 22-case 2 Chronicles evidence-based section identity (source chapter headings, original `scripCom` references, position); (2) verify exact source-to-stock words and section identity for the whole-chapter group; (3) distinguish authored chapter scope from merely a source-book heading; (4) run fully audited, reversible OSIS link construction with no content or occupied-key overwrite, deduplicated chapter presentation and one real reader test. Any new release still requires rights and owner approval. Modern-English #270/#272 remains paused.


## Fourth pass — 117 / 118 source chapter identity and private ordered-word diagnostic (2026-11-14)

**This is the latest measured checkpoint; earlier 96/22 counts are historical.**

At last successful head `5365829188580819ce6f7cc9e4774eeb76700a41`, the independent released native SWORD MHCC module, pinned CCEL ThML, native KJV registry, and source divisions were compared in [full Actions #43617953997](https://github.com/icfmp/Bible-Resources/actions/runs/43617953997) **PASS** (34 targeted tests and complete original inventory). The independent **Validate** suite on the same head is separately tracked and should be checked before any merge.

### Chapter-level structural identity

The original **2 Chronicles** ThML `div1` contains 35 direct chapter `div2` blocks versus 36 KJV chapters. The first `div2` is headed **Chapter 2**. Its original `h2` numeric chapter labels and independent `scripCom` references resolve the off-by-one; the original `div1` book-level *prefix* has two nonempty paragraphs before any `div2`. A similar first-div2 omission occurs in 2 Kings (24 `div2` vs 25 canonical chapters). There is **no directly attributable chapter-one `scripCom` or unambiguous H2 in the 2Chr prefix**. Treat its chapter-one text correspondence as original-source editorial evidence, not a right to silently reassign source markup.

Of the 118 genuine single-key native chapters, **117** have independently coherent source `div2` chapter-body structures: 96 match by complete canonical book/chapter order and 21 match explicit source H2 chapter numbers (2 Chronicles); **1 source `div2` is unassigned: 2Chr.1**.

### Private lexical checks across all 118 unique chapter-body comments

For each single-key native chapter, the exact pinned independent CCEL chapter text (or source `div1` prefix for 2Chr 1) was compared against the exact unchanged compiled CrossWire raw XML. The initial word multiset and independent **existing, bounded** `plain_word_alignment` LCS helper are both diagnostic; **no original prose, markup, citations or verse text was logged or committed**.

- **117** have reciprocal word-multiset overlap at least 95%; **1**, **Neh 1**, falls in the 80–94% class due to original CrossWire raw text including extra words.
- **109 / 118** have exactly identical ordered casefolded Unicode word sequences across source and stock.
- **2 / 118** contain every original CCEL word **in the same order** plus extra CrossWire stock words:
  - **2Chr 1**: CCEL `div1` unwrapped two-paragraph prefix has 129 words, all 129 in identical order within the 131-word native stock body. The **2 extra stock words precede** the 129 exact shared words. This is strong evidence that CrossWire 2Chr.1 preserves that source prefix as a commentary, but source scope / exact-edition typography remains unproven.
  - **Neh 1**: CCEL `div2` has 239 words, all 239 appear in exact order inside 268 native stock words (**29 stock-extra words at the start**). This could reflect an upstream-added title/intro, not automatically content corruption; investigate its markup positions before classification.
- **7 / 118** have a one-word gap on each side of their ordered sequence comparison (one CCEL word and one stock word unmatched). **Gen 38; 2Sam 22; 1Chr 7; 1Chr 17; Job 25; Ps 70; Jer 45.** No lost passage proven; review exact original/source variant and word-token boundary before any edit.
- **No chapters** fall in the “more than ten original words missing in ordered alignment” class. All 118 were within the reviewed alignment budget.

This is **not** a historical Matthew Henry text-parity certificate: headings and source edition differ, punctuation/typography/notes/links/paragraphs have not been matched at full-document precision, and comparisons rely on confirmed scope for the digital original rather than an identical print facsimile.

### Navigation and publication gates

The reader-first indexing policy still holds: when a section is *actually established* as whole chapter, make it discoverable from all canonical chapter verses by **linked references to one unchanged comment**, displayed **once**, never copied as distinct authored comments. A reviewable candidate can be designed against the real 31,102-key KJV registry, with an upper bound of **2,285** possible new navigation keys for these 118 chapters. **None has been added.** The 17 explicit original indexing omissions across 24 missing native keys remain separate from this optional chapter-level navigation upgrade.

**Next:** investigate the seven one-word discrepancies and Neh 1 extra prefix against original XML/stock markup; determine whether 2Chr 1 prefix is genuinely the first chapter exposition rather than a book introduction; verify exact source paragraph and intro fidelity and cross-reference targets before proposing reviewed changes. Keep CrossWire original + BRMHCC 0.1.0 untouched, PR #275 draft, modern-English MHCC #270/#272 paused and any publication blocked until explicit decision.


## Fifth pass — the nine exceptional chapter-body witnesses, original markup positions (2026-11-14)

The full original MHCC stock plus separately SHA-pinned CCEL XML has been
re-scanned on head `bdc7ce7ff3e5b03d0bd892c402465af37ad06883`.
[Editorial scope Action #43619310392](https://github.com/icfmp/Bible-Resources/actions/runs/43619310392)
**PASS** (41 generic editorial tests + 14 read-only link-plan tests), as were
[Validate #43619310411](https://github.com/icfmp/Bible-Resources/actions/runs/43619310411),
[reference targets #43619310358](https://github.com/icfmp/Bible-Resources/actions/runs/43619310358),
[original text #43619310352](https://github.com/icfmp/Bible-Resources/actions/runs/43619310352),
[raw stream #43619310375](https://github.com/icfmp/Bible-Resources/actions/runs/43619310375)
and [source/native research #43619310378](https://github.com/icfmp/Bible-Resources/actions/runs/43619310378).

### Seven isolated one-word source differences

The seven one-word CCEL/CrossWire differences are each a **one-character**
insertion/deletion at the *same word position*. The actual unchanged
CrossWire XML owner was checked with original native text offsets, including
a regression for expanding Unicode casefolds.

| Chapter | Original stock XML owner | Digital-witness edit shape |
| --- | --- | --- |
| Gen 38 | `reference` | one character deleted in stock |
| 2 Sam 22 | root-level tail text | one character inserted in stock |
| 1 Chr 7 | root-level tail text | one character deleted in stock |
| 1 Chr 17 | `reference` | one character deleted in stock |
| Job 25 | `reference` | one character inserted in stock |
| Ps 70 | root-level tail text | one character inserted in stock |
| Jer 45 | root-level tail text | one character deleted in stock |

**Not** seven missing commentary passages; **not** proof that one spelling
or cited reference label should replace the other. The original differing
words and XML never left private CI; the four prose cases still require
exact editorial source review before any change. The three
`reference`-element variations require **independent destination and label
checks**, not an automatic word-normalization rule.

### Two stock-only title/prefix additions

- **2 Chr 1** — all 129 source-prefix words occur in the same order as the
  ending 129 words of the 131-word native entry. The two extra leading words
  are a complete original stock `title` element whose text matches **exactly**
  both the original CCEL `div1 title` attribute and the original preceding
  book H1. This strongly identifies the addition as sourced book-title
  metadata, *not* 2 missing authorial words. The CCEL ThML source body is
  unwrapped in its `div1`, before Chapter 2's first `div2`. However the
  CCEL **web presentation** and a separate digital presentation attribute
  that specific Solomon-themed body to **2 Chronicles chapter 1**:
  [CCEL concise 2 Chronicles page](https://ccel.org/ccel/henry/mhcc/mhcc.xv.html);
  [Christianity.com chapter 1](https://www.christianity.com/bible/commentary/matthew-henry-concise/2-chronicles/1).
  This supplies further strong editorial **chapter-scope corroboration** for
  the previously unassigned source `div1` prefix. It is still not a matching
  print-edition facsimile and not yet an approved compiled link delta.
- **Neh 1** — all 239 original source `div2` words occur in the same order
  as the final 239 words of the 268-word original stock entry. The 29 extra
  leading words include a separate original stock `title` element whose
  text matches **exactly** the source CCEL `div1 title` attribute.
  Original source-body word boundary lies *within another stock title*;
  provenance/typography of all extra leading words remains to be reviewed.
  The 239-word authorial body was not demonstrated lost.

Both stock/source suffixes have one punctuation/nonword gap difference by
the existing text-free comparator. This requires fidelity review but cannot
be called an error without checking the exact digital edition conventions.

### Cautions and next gate

This diagnostic is **non-destructive** and source-neutral. It never exports
the original differing word values, modifies source text or assumes
that a `scripRef` citation is the anchor of a commentary section.

**Next:** review all seven one-character differences with a trustworthy
identified edition; test the three navigational citation destinations;
independently verify the chapter-first heading and original source
introduction semantics, including 2 Chr 1 and Neh 1; then prepare an
*explicitly reviewed* candidate full-verse linked-index map, correct separate
disjoint spans (e.g. Matt 13), and test deduplicated rendering in a real
reader. The exact original CrossWire module and published BRMHCC 0.1.0
remain unchanged, and modern English #270/#272 is paused.


## Sixth pass — reference preservation and safe unbuilt link-preflight (2026-11-14)

The independently pinned CCEL ThML source and the complete SHA-pinned original
CrossWire MHCC zCom were compared **for every one of the 118 single-key
chapters**, using the existing strict source `scripRef` versus compiled
`reference osisRef` comparator. The comparison checks exact raw targets first,
then **only** the *literal* optional `Bible:` work prefix; it never invents
canonical destinations from displayed labels.

Reproduction:
- [Whole 118-case reference target census — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43621130646)
- [Original source labels versus unlinked compiled text — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43621365477)
- [Complete canonical original-native key preflight — SUCCESS](https://github.com/icfmp/Bible-Resources/actions/runs/43621652881)

### Exact source-vs-stock target inventory

| Cross-edition reference markup class | One-key chapter entries |
| --- | ---: |
| Neither original nor stock has annotated scripture reference targets | **79** |
| Every reference target matches exactly or by literal `Bible:` work prefix | **19** |
| Source has at least one target, selected stock entry has no `reference` tags | **16** |
| Source has more target occurrences than matching target occurrences in stock | **4** |
| Stock has unpaired source-absent target occurrence | **0** |
| **Total** | **118** |

- Original CCEL source `scripRef` target occurrences: **58**.
- Original CrossWire stock `reference` target occurrences: **33**.
- Paired original/stock target occurrences after exact / literal `Bible:` prefix matching: **33**.
- **25 CCEL-annotated citation target occurrences are not linked** in those
  selected original stock entries, across **20** single-key chapters.
  This is a *cross-edition annotation fidelity difference*, NOT proof of
  authorial word loss or 25 independently approved corrections.
- In **16** of those chapters, stock has **zero link-markup targets** where
  original CCEL has **20** source citation labels. Of those 20 labels,
  **16** still occur literally in stock plain text, **2** occur as word
  sequences with different punctuation/markup, and **2** cannot be located in
  the selected stock entry at all.
- The other **four** partial-reference chapters are **2 Sam 22, 1 Chr 17,
  Psalm 16 and Psalm 53** (5 source unpaired targets).
- Three one-word stock XML `reference` label variants require special
  care: **Gen 38** and **Job 25** retain both independently source-matched
  `osisRef` targets (2/2) and differ only in displayed label spelling;
  **1 Chr 17** retains only 2 of 4 original CCEL reference target
  occurrences in the selected stock body. An original target presence check
  **does not validate that it points to the intended verse in a reader**.

The existing global lexical/reference audit in issue #177 previously revealed
unpaired `scripRef`/stock `reference` annotation differences in **other**
selected commentary sections. This 118-chapter census is a complementary
bounded audit of chapter-wide units, **not** the complete corpus-wide
cross-edition source/target fidelity certificate.

### Canonical missing section preflight

A new **reusable, read-only** `triage_missing_native_section_links` in
`scripts/commentary_navigation_link_plan.py` takes the independently
read original native occupied-key-to-raw-digest map, actual released libSWORD
KJV registry and the full parsed heading-gap list. It checks original master
digest presence, canonical target key bounds, *actual* target vacancy,
cross-section double claims and original payload collisions.

The complete exact-stock source run reports **17 candidate sections,
24 unoccupied canonical verse keys, zero collisions with already occupied
different original commentary sections**. The disjoint Matt 13 section
remains 24–30 **and** 36–43, leaving the genuinely different 31–35
commentary alone. **No original raw content, linked key, verse number,
index file or release was edited**, and the output carries
`editorial_approval=false` and `release_authorized=false`. It is **not
yet a build-ready proposal** and cannot be passed through the guarded
`propose_commentary_links` without individual scope review.

### Next editorial decisions (not automatic corrections)

1. Locate the four apparent prose one-character differences inside the
   original independent XML `scripRef` label offsets, **not just** the
   compiled stock `reference` element offsets. A flattened source citation
   can look like ordinary compiled prose; it must not be misclassified as an
   authorial prose rewrite.
2. Review the two source labels not found in selected compiled entry,
   plus the five partial-section citation annotations, against their
   own source passage divisions and another independently identified
   edition before any markup reconstruction.
3. Check original verse/passage ranges, chapter-level unit scope, all
   notes/paragraphs/intro relationships and the exact source edition
   rights. Produce a **separate, reversible candidate** only after these
   gates; confirm all original keys/raw payloads and one real reader's
   behavior. Owner approval remains required for publication, and paused
   modern-English #270/#272 must not restart prematurely.


## Seventh pass — resolve the original XML owner of all seven one-word variants (2026-11-14)

The source XML versus native word-offset check is now independently tested
against actual **original CCEL `scripRef` markup offsets**, rather than
classifying words solely from their *compiled stock* XML location.
[Full original SWORD/ThML audit #43621876487](https://github.com/icfmp/Bible-Resources/actions/runs/43621876487)
**PASS** on exact native module and SHA-pinned independent source. The 118-case
review identifies:

| Chapter | Original CCEL changed-word owner | Compiled CrossWire changed-word owner |
| --- | --- | --- |
| Gen 38 | `scripRef` citation label | `reference` |
| 2 Sam 22 | `scripRef` citation label | unlinked root-level text |
| 1 Chr 7 | **outside any** `scripRef` label | unlinked root-level text |
| 1 Chr 17 | `scripRef` citation label | `reference` |
| Job 25 | `scripRef` citation label | `reference` |
| Ps 70 | `scripRef` citation label | unlinked root-level text |
| Jer 45 | `scripRef` citation label | unlinked root-level text |

**Consequences:** Six of the seven one-character text differences are
**source scripture-citation label variations**. Three are displayed in
compiled linked references, and three are flattened into unlinked compiled
text. Only **1 Chr 7** is a different word in the **commentary prose outside
a source `scripRef`**. It is a *digital-witness variant*; no print-edition
authority has yet resolved which form is authorial. Neither original word
was exposed outside the restricted comparison. No source spelling or
punctuation has been edited.

The source `scripRef` is a citation element, not proof that it should be
a chapter annotation anchor. Correct future treatment requires preserving
the original link's intended OSIS target *and* the author's visible wording
where independently verified, rather than arbitrarily adding a hyperlink
around a similar string.

**Current decisions:** retain all 118 original source/commentary bodies
unchanged; keep 17/24 range-index **preflight** separate from proposed
chapter-wide access; review 25 source-vs-stock missing link target
occurrences before reconstructing markup. Source-to-stock content
integrity is not yet accepted globally. The modern-English translation
remains paused.


## Eighth pass — standards-based native link strategy, synthetic evidence and driver limits (2026-11-14)

This implementation checkpoint is deliberately **not a MHCC reindexing or new edition**. The only compiled binaries created for these experiments are synthetic, source-original text authored solely for tests, installed in isolated temporary runner directories.

**Standard OSIS commentary linked-section proof:** `tests/fixtures/synthetic-linked-commentary.osis.xml` has three different independently worded comments: a contiguous range, an independent intervening section, and a discontinuous range with an intentionally vacant key in the middle. In [CI #43622505845](https://github.com/icfmp/Bible-Resources/actions/runs/43622505845), the released `osis2mod` zCom importer created the module and our independently compiled original native SWORD raw reader verified:
- All seven expected occupied synthetic verses read back their full original comment text.
- All linked members of the same source section returned byte-identical raw payloads.
- The intervening independently authored section did not get overwritten.
- The deliberately unannotated gap stayed empty.

Therefore **standards-based OSIS continuous and discontinuous commentary annotation is independently viable** with the installed released SWORD engine; this neither certifies the original MHCC's content parity nor guarantees that all viewers deduplicate linked entries.

**Direct modification of an existing compiled module is not assumed possible.**
A second isolated proof attempted calling the public `zCom::linkEntry` method on a copied synthetic module whose compressed authorial `.czz` data files were independently SHA-256 recorded before modification. The stock released-libSWORD module loaded via `SWMgr` reports `isWritable()==false`. This is consistent with the actual SWORD 1.9 zCom constructor passing `-1` for zVerse file mode, which is mapped to `FileMgr::RDONLY`. See:
- https://www.crosswire.org/sword/apiref/zcom_8cpp_source.html
- https://www.crosswire.org/sword/apiref/zverse_8cpp_source.html

A **fail-closed capability** regression therefore records `SYNTHETIC_NATIVE_ZCOM_READ_ONLY`: the synthetic copied original raw entries must remain identical and no link is inserted. The test must **not** modify compressed records or patch .czv index bytes outside the supported SWORD API. A writable-mode constructor or alternative official importer must be demonstrated with lossless readback before an index-only path is proposed.

**Implementation direction:** prefer a **new, separately identified standard OSIS-derived SWORD edition**, but only after the precise original source content, topology, XML metadata, rights and passage scopes are sufficiently verified to guarantee no authorial words/notes/links lost or rewritten. Existing original MHCC 2.0 and BRMHCC 0.1.0 always remain immutable witnesses. Existing cross-edition differences of 25 source reference target occurrences and the one actual 1 Chr 7 prose variant are unresolved; do not mechanically choose CCEL text as a replacement original.

**Release gates:** independently verified full source+stock text and structure parity, exact compiler/readback of 29,975 original occupied keys including intros and TOP, deterministic reversible mapping receipts, collision-free 17 explicitly justified section gaps, separate reviewed chapter-wide navigation scopes, correct citation destinations, one authentic independent reader, deduplicated presentation, approved rights and explicit publication authorization. Failing any gate leaves the new module unpublished and the modern-English translation paused.
