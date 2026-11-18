# UBS Hebrew Bible dictionary — bilingual MACULA WLC crosswalk (v0.1)

This is a **compact lexical index**, not a rewritten dictionary. It joins the
pinned Macula WLC word annotations to the shared, original stable identifiers
of the **UBS Dictionary of Biblical Hebrew** in French and English.

## Source and rights

- Original EN: [UBSHebrewDic-v0.9.4-en.JSON](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-en.JSON)
- Original FR: [UBSHebrewDic-v0.9.4-fr.JSON](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-fr.JSON)
- Fixed UBS commit: `a15a96cfaa4ca18a6c0339016645ba1e534db3c8`
- Original [MACULA Hebrew WLC TSV](https://github.com/Clear-Bible/macula-hebrew/blob/47db250bd55d0d8577f2a94fba114ef16c35b23c/WLC/tsv/macula-hebrew.tsv), fixed revision `47db250bd55d0d8577f2a94fba114ef16c35b23c`.
- Original dictionary copyright © United Bible Societies; adapted from the **Semantic Dictionary of Biblical Hebrew**. Source license **CC BY-SA 4.0**, preserving UBS attribution and ShareAlike. MACULA linguistic annotations: **CC BY 4.0**, credited separately.

No UBS definitions, translations, lexicon articles, or original Macula word text are copied into the crosswalk. They remain in their licensed source datasets and must be read there. This index only contains verifiable relationships between lexical identifiers and edition/revision metadata.

## Key finding: exact `sdbh` pointers

MACULA WLC already has an `sdbh` field which, when present and attested in the exact UBS edition, can identify a **specific UBS `LEXID` sense**, not just a headword.

The complete source comparison found:

| Metric | Count |
| --- | ---: |
| Shared UBS MainId entries, EN/FR | 7,943 |
| Shared UBS LEXID senses, EN/FR | 16,619 |
| EN/FR lexical identifier drift | 0 |
| Full Macula WLC source word rows | 475,911 |
| WLC rows with populated `sdbh` | 244,734 |
| WLC rows whose `sdbh` exactly matches a UBS sense | 165,214 |

## Full generated index coverage

The source-pinned generator was executed against all 475,911 WLC rows:

| Link classification | Occurrences |
| --- | ---: |
| Exact UBS sense (`sdbh` → `LEXID`) | 165,214 |
| Single UBS headword via language-specific Strong, **sense unknown** | 113,314 |
| Multiple candidate UBS headwords via Strong, **ambiguous** | 2,741 |
| Numeric Strong without a matching dictionary entry | 40,747 |
| Unsupported / non-numeric or otherwise unverifiable lexical link | 153,895 |
| **Total** | **475,911** |

**281,269 / 475,911 (59.1%)** have at least one UBS entry candidate, but only **165,214 (34.7%)** have an exact sense match. These are measured results for **these pinned source editions**, not a claim that all remaining original Greek/Hebrew words lack dictionary definitions. We do **not** collapse suffixes, infer from spelling, or silently reinterpret source `sdbh` IDs to increase percentages.

The other source `sdbh` pointers **must not be fabricated or silently remapped**: the source has more values than are attested in the pinned dictionary edition. The index returns the relevant entry *only* when an independently exact matching original `Strong` code exists, with `entry_only` status, **never** a guessed contextual sense. A match to multiple entries returns the complete candidate list.

## Index design

- `by_sdbh`: exact fifteen-digit original Macula `sdbh` sense ID → one or more stable UBS `MainId` values. The `sdbh` value itself is the exact `LEXID` sense.
- `by_strong`: language-aware, numeric-only `H` (Hebrew) / `A` (Aramaic) Strong ID → zero or more stable UBS `MainId` values. Suffixes, compound identifiers, and ambiguous forms are not guessed.
- `coverage`: complete WLC audit, distinguishing exact senses, entry-only fallback, ambiguous entries and unmatched words.
- `statistics`: bilingual lexical ID inventory and excluded forms.

Lookup order for one original WLC word: try the exact `sdbh` sense first; if no exact UBS sense is present, try the *language-specific* numeric Strong headword only. An unsupported or missing match returns an explicit no-link result. An `entry_only` result is **not an assertion that any one dictionary meaning applies**.

The index is shared by French and English: use the same `MainId`/`LEXID` to open the corresponding language edition. No second set of lexical links needs to be built.

## Connection to BSI entities

BSI and the dictionaries share the original Macula word anchor but answer different questions:

- `BSI → original word`: who or what is being referred to?
- `original word → UBS lexeme / sense`: what lexical meaning(s) are available?

No entity identity is inferred from a shared lemma, spelling or Strong code. Dictionary article content stays outside the BSI core, and encyclopedia crosswalks belong under `links/encyclopedias/`.

## Reproducibility

```bash
python3 -I entity-index/links/dictionaries/ubs-hebrew/test_index.py

python3 -I entity-index/links/dictionaries/ubs-hebrew/build_index.py \
  --english ubs/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-en.JSON \
  --french ubs/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-fr.JSON \
  --macula macula-hebrew/WLC/tsv/macula-hebrew.tsv \
  --output entity-index/links/dictionaries/ubs-hebrew/index.json
```

The [GitHub Actions workflow](../../../../.github/workflows/bsi-ubs-hebrew.yml) uses exact source revisions and UBS file blob hashes, verifies all word rows, and compares the generated output with the committed index. No upstream resource is modified.
