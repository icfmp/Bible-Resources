# MHCC — cross-edition lexical review after original source-book identity gating

**Research-only checkpoint, 2026-11-13 — source edition comparison, not a release authorization.**

This memo reconciles the previously published **156** CCEL-to-CrossWire word-selection differences with the independent **10** source-versus-compiled discrepancies remaining after authentic `scripRef` / `reference` label-word exclusion. It identifies **five comparisons invalidated by conflicting original source metadata**, not five missing or corrected commentary passages. Every datum is from actual SHA-pinned original material and a full repeatable GitHub Action; no source, annotation, reference or binary was changed.

## Exact input witnesses

| Source | Identity |
| --- | --- |
| Original CCEL ThML independent witness | SHA-256 `4a5509ba5064b54572397ae1a796561ff6ce4a1e18f366af0141a09c5d06fcd6` |
| CrossWire original MHCC 2.0 ZIP | SHA-256 `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d` |
| Complete native original SWORD corpus (all **29,975** occupied slots) | SHA-256 `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6` |
| Reproducible exact-head implementation | [PR #225](https://github.com/icfmp/Bible-Resources/pull/225), merged commit `a5dcecc732753bc682d962221e56f2409f731106` |
| Full source + native compiled comparison | [GitHub Action #43501597180](https://github.com/icfmp/Bible-Resources/actions/runs/43501597180), **SUCCESS**, metadata artifact `commentary-private-text-compare-receipt` (artifact 14073569033) |
| Independent complete test suite | [Validate #43501597178](https://github.com/icfmp/Bible-Resources/actions/runs/43501597178), **SUCCESS** |

The generic `classify_lexical_source_identity()` joins **source line + original full-reference SHA-256 + original authorial-body SHA-256** before comparing the source division's **actual SHA-attested heading** with the source's **actual claimed OSIS book code**, using the existing canonical 66-book English alias metadata. It rejects altered headings, ambiguous attribution, duplicate identities and substituted hashes. This does **not** rewrite an original book code or justify silently switching a reference to another book.

## Decision queue from actual full corpus review

| Original CCEL XML line | Unmatched original prose words in stock order | Source title / claimed book identity | Decision |
| ---: | ---: | --- | --- |
| **441** | 1 | Consistent | Small different-edition lexical review |
| **4,291** | 2 | Consistent | Small different-edition lexical review |
| **9,727** | 1 | Consistent | Small different-edition lexical review |
| **15,219** | 59 | Consistent | Substantial different-edition source/section review |
| **28,749** | 172 | Consistent | Substantial different-edition source/section review |
| **55,844** | 334 | **Contradiction** | Quarantine: unsafe original source-to-stock book join |
| **55,852** | 178 | **Contradiction** | Quarantine: unsafe original source-to-stock book join |
| **55,858** | 467 | **Contradiction** | Quarantine: unsafe original source-to-stock book join |
| **55,868** | 245 | **Contradiction** | Quarantine: unsafe original source-to-stock book join |
| **55,875** | 198 | **Contradiction** | Quarantine: unsafe original source-to-stock book join |

**Measured totals:** 10 original unresolved non-reference-prose word comparisons = **5 same-book independent-edition comparisons + 5 original-source book-identity conflicts**. The five comparable cases divide into **3 one/two-word differences** and **2 substantial word-order/selection differences**. Do not convert these measurements into a claim that an edition is right or wrong.

The **five quarantined** original source comments lie within a ThML `div1` whose **actual English original heading is Jude**, while its five original `scripCom` references claim **Judg (Judges)**. Comparison against CrossWire **Judges** comments on the strength of that contradictory source field alone falsely attributes independent-book prose differences to the stock module. [Original source title/bookcode evidence](one-original-title-jude-vs-judg-osis-conflict.json) and [four source units sharing one native raw run](four-original-source-units-two-div1-in-one-native-raw-run.json) corroborate the problem. The authorial original title **and** the erroneous-looking original OSIS values remain unchanged; the precise correction belongs to the source maintainer and editorial reviewer.

## Remaining work, properly separated

1. **Editorial, if pursuing CCEL-to-CrossWire parity:** examine three small and two substantial **same-book** differences against their exact printed/digital edition provenance, citations, range mapping and structure. These are **not** proof of errors in the unchanged CrossWire module; using CCEL to reconstruct CrossWire is a different production track with full source and rights requirements.
2. **Original CCEL source identity:** review the five conflicting Jude/Judges markers and, if independently confirmed, propose a correction upstream. Do not alter the input file, its title or reference mapping merely to suppress test failures.
3. **Exact stock reuse track:** the [generic commentary workflow](../../COMMENTARY_7_STAGE_WORKFLOW.md) permits an unmodified, pinned upstream SWORD witness with independent complete compressed-byte / raw-key identity, while honestly documenting that a different digital witness is not proven textually equal. The private `BRMHCCReview` candidate passed the full-stock identity tests, actual Xiphos commentary reading **5/5**, and original hyperlink href parity **2/2** in [PR #224](https://github.com/icfmp/Bible-Resources/pull/224).
4. **Still independent publication gates:** exact digital-transcription redistribution rights and owner editorial approval, visual titles/heading position, actual link clicking/navigation, reader scope as required by the project's process, package/catalogue integrity and formal publication decision. See [rights dossier](crosswire-exact-stock-rights-review.md) and [issue #177](https://github.com/icfmp/Bible-Resources/issues/177). **No MHCC public release has been made.**

These are **ten reviewed comparison records**, not ten editorial changes. Historical original-to-stock audit counts remain available, and no original resource content, punctuation, titles, notes, verse numbers, reference strings or compiled ZIP content has been rewritten.
