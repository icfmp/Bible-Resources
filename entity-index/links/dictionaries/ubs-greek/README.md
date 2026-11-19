# UBS Greek NT Dictionary — bilingual lexical bridge (v0.1)

This **real, reproducible** lookup index links pinned Macula Greek SBLGNT lexical
annotations to stable UBS Dictionary of the Greek New Testament **edition 1.0**
entry and semantic-sense IDs. It works for **English and French** without
creating different lexical IDs for each language.

## Files

- [index.json](index.json): **generated compact bridge**, containing only
  `by_strong` (Macula numeric Strong → UBS `MainId[]`) and `by_ln`
  (Macula Louw–Nida code → pairs of UBS `MainId`, `LEXID`).
- [build_index.py](build_index.py): exact-schema, bilingual ID-parity validation,
  deterministic generation, and full Macula token coverage audit.
- [test_index.py](test_index.py): ambiguity, source parity and no-false-guess tests.
- `source/` and `work/` can be local Git-ignored checkout/research folders;
  the actual immutable original datasets stay in their existing official
  upstream repositories rather than duplicating 30 MB in our repo.

## Pinned inputs

- UBS [English v1.0](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/greek/JSON/UBSGreekNTDic-v1.0-en.JSON)
- UBS [French v1.0](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/greek/JSON/UBSGreekNTDic-v1.0-fr.JSON)
- Pinned revision: `ubsicap/ubs-open-license@a15a96cfaa4ca18a6c0339016645ba1e534db3c8`.
- Macula Greek [SBLGNT TSV](https://github.com/Clear-Bible/macula-greek/blob/8423afe47b9e8f24b7772e808af45c7159a6fe7e/SBLGNT/tsv/macula-greek-SBLGNT.tsv):
  `Clear-Bible/macula-greek@8423afe47b9e8f24b7772e808af45c7159a6fe7e`.
- [UBS dictionary license](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/greek/LICENSE.md):
  **CC BY-SA 4.0**; © United Bible Societies. The lexicon adapts the work of
  Louw and Nida as described in its source README. Credit original editors
  and upstream publishers in redistribution notices.
- MACULA linguistic dataset: **CC BY 4.0**, separately credited.

**Why use v1.0 in both languages?** These two source files have **identical
5,507 `MainId` inventories and 9,160 `LEXID`/semantic-code assignments**,
even though their definitions differ by language. A more recent English v1.1
and French v1.01 pair exists, but three entries have sense-structure drift; do
not silently assume that mismatched editions are interchangeable.

## Confirmed coverage against the pinned Macula words

| Metric | Count |
| --- | ---: |
| Greek UBS entries (shared EN/FR) | 5,507 |
| Greek UBS senses (shared EN/FR) | 9,160 |
| Indexed Strong numbers | 5,218 |
| Indexed Louw–Nida codes | 7,087 |
| Macula Greek source word rows | 137,741 |
| Words with at least one UBS entry candidate | 128,090 |
| Words with corresponding UBS sense candidates | 118,272 |
| Words with more than one candidate UBS entry | 224 |
| Words without a matched UBS entry | 9,646 |
| Compound/unsupported Strong patterns, not guessed | 5 |

These are **lexical coverage counts**, not historical BSI entity coverage
or certification that one exact contextual sense has been determined.

## Lookup contract

Given a **real pinned Macula original word ID**:

1. Read its `strong` and `ln` attributes from the pinned Macula TSV.
2. Use the exact numeric Strong ID to obtain zero or more UBS `MainId`
   values from `index.json/by_strong`. Explicit suffixes such as `G1003b`
   are **not silently collapsed** into `G1003`.
3. Take all exact Louw–Nida codes from Macula `ln`, read candidate
   `(MainId, LEXID)` pairs from `by_ln`, **and keep only pairs whose
   parent MainId belongs to the Strong-derived entries**.
4. For the requested language, fetch the UBS record keyed by `MainId` and
   the entry's `LEXID` sense. The bridge contains **no definitions or glosses**.
5. When no entry or no intersection is available, return an explicit
   unmatched/entry-only status. When multiple candidates remain, return all
   candidates; never pick a meaning by first-match, dictionary order, or
   spelling alone.

**Example:** Matthew 1:1 `n40001001003` is annotated with Strong `2424`,
which resolves to UBS `MainId=002427000000000`. The specific `ln` code
can further narrow the dictionary `LEXID` candidates. The exact IDs are
the same for FR and EN; the definition text is not.

### Relation to BSI entities

The BSI `by_word` lookup already links entities to original words.
The UBS bridge instead links **original-word lexical annotations** to UBS
entries. Therefore the sequence is BSI entity → original word → Macula
Strong/LN → UBS lexical candidate. It is **not** an assertion that a
dictionary lemma definition uniquely describes a biblical person or place.
Encyclopedia crosswalks remain separate under `links/encyclopedias/`.

### Rebuild and audit

With separately pinned original sources checked out:

```bash
python3 -I entity-index/links/dictionaries/ubs-greek/build_index.py \
  --english ubs-source/dictionaries/greek/JSON/UBSGreekNTDic-v1.0-en.JSON \
  --french ubs-source/dictionaries/greek/JSON/UBSGreekNTDic-v1.0-fr.JSON \
  --macula macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv \
  --output /tmp/ubs-greek-rebuilt.json
python3 -I entity-index/links/dictionaries/ubs-greek/test_index.py
```

The [automated workflow](../../../../.github/workflows/bsi-ubs-greek.yml)
verifies the exact upstream revisions and blob IDs, rebuilds against both
language source files and the full Macula TSV, and structurally compares
the generated index with the committed version. **No source file is modified.**

## Exact-source Greek gap register (v1 editorial intake)

The original 137,741 SBLGNT word rows are untouched. A source-pinned,
reproducible [read-only audit](audit_source_gaps.py) and its
[negative unit tests](test_source_gaps.py) give every currently unmatched
word a source-specific disposition and verify each original source word ID.

**Editorial intake only, not accepted links or publication:**

| Original source category | Original word occurrences |
| --- | ---: |
| Existing matched UBS headwords (unchanged baseline) | 128,090 |
| One Unicode-NFC-identical UBS headword **plus** matching source Louw–Nida code | **5,938** |
| One Unicode-NFC-identical UBS headword, **without** matching UBS source semantic code | **3,249** |
| No Unicode-NFC-identical UBS headword | **459** |
| Source Strong annotation is composite/unsupported | **5** |
| **Original MACULA Greek SBLGNT words** | **137,741** |

The 9,651 original words lacking a direct entry occupy **238 families after
Unicode NFC canonical equivalence**, as opposed to **246 distinct original
byte-spelled Strong/lemma pairs**. This is a *comparison-only* grouping.
All original Greek lemmas, token word IDs, morphologies, Louw–Nida codes,
Strong numbers and source verses are retained in the evidence register.

NFC accepts canonical Unicode equivalents such as `ἐγώ` and `ἐγώ`,
but **never strips accents** or infers identity from similar transliterations.
The compatible word-by-word list is an **unapproved candidate inventory**:
a common Louw–Nida code supports a headword comparison, not a unique
contextual sense. Rejected/missing/homonymous cases are not secretly
redirected to a different original Strong code.

**Known source-specific constraint:** UBS Greek v1.0's original `εἰμί`
headword (`G2258`) has no `LEXMeanings` records. MACULA does
annotate other inflected forms of `εἰμί` (e.g. `G2076`, `G1510`)
with Louw–Nida codes. These are *not* independently verified UBS
contextual sense IDs. Such rows stay outside the strict two-source
word-link candidate list until reviewed on a separate evidentiary basis.

GitHub Actions regenerates the complete source evidence from the **same
pinned UBS Greek v1.0 EN/FR and MACULA SBLGNT revisions** used in the
existing release-compatible index; it verifies exact coverage counts,
bilingual entry/sense-ID parity, canonical lemma matching and all
original word IDs. The temporary report is uploaded only as a
**NOT-PUBLISHED, UNAPPROVED** Actions artifact. The frozen, historical
[index.json](index.json) remains unchanged.

Editorial follow-up is tracked in [issue #396](https://github.com/icfmp/Bible-Resources/issues/396).
