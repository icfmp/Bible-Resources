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
