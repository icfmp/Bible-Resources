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
