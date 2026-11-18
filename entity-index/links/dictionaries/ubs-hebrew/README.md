# UBS Hebrew dictionary — source-guarded bilingual MACULA WLC crosswalk

This source-pinned index links MACULA WLC words to **UBS Dictionary of Biblical Hebrew 0.9.4 (EN/FR)** without copying definitions. Lexical correctness and edition identity take priority over a high coverage percentage.

## Original editions, provenance and rights

- [UBS English 0.9.4](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-en.JSON) and [UBS French 0.9.4](https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/hebrew/JSON/UBSHebrewDic-v0.9.4-fr.JSON), commit `a15a96cfaa4ca18a6c0339016645ba1e534db3c8`.
- [MACULA Hebrew WLC](https://github.com/Clear-Bible/macula-hebrew/blob/47db250bd55d0d8577f2a94fba114ef16c35b23c/WLC/tsv/macula-hebrew.tsv), commit `47db250bd55d0d8577f2a94fba114ef16c35b23c`.
- UBS copyright © United Bible Societies, **CC BY-SA 4.0**; MACULA source **CC BY 4.0**. Keep original attributions and ShareAlike obligations. Neither dictionary prose nor original WLC text is redistributed in this index.
- Source inventories: 7,943 matching UBS EN/FR headword IDs and 16,619 sense IDs, with zero EN/FR identifier drift in these pinned files.

## Critical edition-identity correction

An earlier index trusted the fact that a 15-digit MACULA `sdbh` identifier also occurred as a UBS `LEXID`. **This is not a sufficient identity check across source editions**. The full corpus comparison demonstrated that identical numeric identifiers can refer to unrelated lexemes.

For instance, WLC Genesis 1:1 annotates `רֵאשִׁית`, Strong H7225, with `sdbh=006653001001000`. In this UBS edition, `006653001001000` belongs to `רֹאשׁ`, whose Strong codes are H7218, H7219 and H7220. The old direct-sense link was not established by a genuine lexical identity match.

The new generic `lookup(index, sdbh, strongnumberx, lang)` enforces **independent numeric Strong-family corroboration** for every direct `sdbh` candidate. It verifies the original H/A language and the numeric Strong base against the actual owning UBS headword. When those differ, the direct sense is **quarantined**; only the **original exact** Strong value (including a letter suffix, if present) may yield an `entry_only` fallback. An unmatched word is left unresolved. Original source data and IDs are never modified.

This conservative check validates the **lexeme identity** supporting a candidate sense ID. It is *not* proof that sense inventories remain semantically identical between editions. Do not market the retained direct matches as independently editorially validated contextual meanings.

### Full corpus results after quarantine

| WLC occurrence outcome | Count |
| --- | ---: |
| Corroborated UBS source sense ID (Strong numeric family agrees) | **30,492** |
| Single UBS headword via exact Strong, contextual sense unknown | **221,522** |
| Multiple UBS headwords via exact Strong, ambiguous | **5,024** |
| Exact Strong without a corresponding UBS entry | **218,868** |
| Unsupported Strong structure | **5** |
| **Total original WLC word occurrences** | **475,911** |

**257,038 / 475,911 (54.0%)** have at least one verifiable headword candidate; **30,492 (6.4%)** retain a source sense ID with corroborating Strong-family evidence. Compare the previous **283,219** linked occurrences and **165,214** raw equal-ID matches; those historical numbers counted links which may cross into unrelated lexemes, and must not be used as present accuracy figures.

A separate source-identity audit counts the former 165,214 raw numeric `sdbh` overlaps:

| Independent lexical evidence for equal-ID entries | Original WLC rows |
| --- | ---: |
| Identical lemma and identical Strong | 17,378 |
| Identical lemma and same Strong numeric family (suffix differs) | 6,329 |
| Different lemma spelling but identical Strong | 5,879 |
| Different lemma spelling but same Strong numeric family | 906 |
| Same lemma with different or missing Strong | 804 |
| **Different lemma and different Strong family (untrusted)** | **133,918** |
| **Total raw equal-ID rows** | **165,214** |

The first four classes above sum to **30,492**, matching the new corroborated count. The 804 exact spelling matches without Strong corroboration are deliberately not promoted to an authoritative sense. Similar spelling alone is insufficient.

### Content-word coverage

MACULA classes `noun`, `verb`, `adj`, `adv`, `num` contain 248,680 source occurrences:

| Metric | Occurrences |
| --- | ---: |
| Corroborated source sense IDs | 29,449 |
| UBS entry-only matches | 199,256 |
| Unresolved | 19,975 |
| **With UBS headword** | **228,705 (91.97%)** |

This is coverage of **selected original WLC source classes**, not the dictionary's theoretical completeness or the number of distinct lexemes. Grammatical morphemes remain part of the full WLC denominator.

## Reconciliation candidates — not accepted links

The separately generated [reconciliation_candidates.json](reconciliation_candidates.json) contains **508 original lemma + Strong-family candidate groups**, representing **7,588 occurrences** among the current 19,975 unresolved lexical occurrences. To enter the *review-only* file, a group requires identical NFC lemma, matching H/A numeric Strong family, and a unique original UBS headword. The suffix schemes may differ; that is **not evidence of an exact Strong code**, and **no candidate is added to the authoritative dictionary lookup**.

A further **12,385** lexical occurrences have no such joint evidence, and 2 lack supported source Strong syntax. Frequent groups include `עַיִן`, `קוֹל`, `פֶּה`, `טוֹב`, `שַׁעַר`, `רַע`. In particular, `כֹּל` (H3605) has no matching UBS original Strong/headword in this edition and must not be linked using its numerically coincident `sdbh` parent.

## Verified improvement: original-word-anchored headword links

The pinned WLC source and UBS Hebrew 0.9.4 confirm **2,695 additional
entry-only links** beyond the conservative four-field lookup. The word-aware
path is deliberately **not** an alias from unsuffixed Strong to suffixed
Strong: such a rule could conflate homonyms.

A link is permitted only when **all** of the following hold for an original
MACULA WLC source word:

1. Its ordinary exact source `sdbh`/Strong lookup has no UBS entry.
2. Its original source class is `noun`, `verb`, `adj`, `adv`, or `num`.
3. Its exact NFC lemma equals the UBS headword's original lemma.
4. Its H/A numeric Strong family identifies **exactly one headword across
   the entire UBS source**, including entries with different suffix letters.
5. Its **original complete MACULA word ID** is retained; source lemma,
   Strong code, and language must also match at lookup.

The new `lookup_word(index, word_id, sdbh, strongnumberx, lang, lemma)`
accepts that original word identity and returns **entry-only** evidence
(`sense_ids=[]`). It rejects mismatched original source fields instead of
silently picking a different entry. The existing four-argument
`lookup(index, sdbh, strongnumberx, lang)` stays unchanged and conservative
for callers that do not have WLC word IDs.

| Measure | Generic exact-source path | Original-word-aware path |
| --- | ---: | ---: |
| WLC occurrences with a candidate UBS headword | 257,038 | **259,733** |
| Additional unique-source headword links | — | **2,695** |
| WLC occurrences with Strong-corroborated SDBH sense IDs | 30,492 | **30,492** |
| Selected lexical-class occurrences with an UBS headword | 228,705 | **231,400** |
| Selected lexical-class coverage | 91.97% | **93.05%** |

Both paths remain pinned to the **same unmodified UBS and MACULA editions**.
The word-anchored path is an opt-in query using a frozen original MACULA
word ID; it cannot safely be substituted by a general Strong-prefix lookup.
No contextual sense is inferred, no original `sdbh` is rewritten, and
dictionary prose is unchanged.

The generator now stores `by_macula_word` plus
`coverage_with_word_ids` in [index.json](index.json); the
[full original-corpus CI](../../../../.github/workflows/bsi-ubs-hebrew.yml)
rebuilds both and verifies **2,695** new links and **259,733**
word-aware candidates. [test_word_anchored.py](test_word_anchored.py)
tests source identity isolation, H/A separation, ambiguous UBS Strong
families, and preventing cross-edition `sdbh` collisions.

## Source integrity and test workflow

- [build_index.py](build_index.py) produces `index.json`, preserving `by_sdbh` and `by_strong`, adding `by_entry_strong_family` for corroboration and retaining full coverage statistics. The generated index never contains dictionary definitions.
- [audit_direct_sense_fidelity.py](audit_direct_sense_fidelity.py) measures 165,214 raw equal-ID overlaps against independent MACULA/UBS lemmas and Strong identities.
- [audit_unmatched.py](audit_unmatched.py) categorizes unresolved original rows; [audit_variants.py](audit_variants.py) reports source morphology and lexical-class coverage.
- [audit_lexical_gaps.py](audit_lexical_gaps.py) groups unresolved lexical occurrences by original language/lemma; [audit_top_lemmas.py](audit_top_lemmas.py) examines frequent problem families.
- [audit_strong_reconciliation.py](audit_strong_reconciliation.py) reconstructs the **review-only** candidate report. Its original word-ID witnesses allow review without inventing entries.
- [test_index.py](test_index.py), [test_lexical_gaps.py](test_lexical_gaps.py), [test_strong_reconciliation.py](test_strong_reconciliation.py), and [test_word_anchored.py](test_word_anchored.py) include offline synthetic regression tests.
- The [GitHub Actions workflow](../../../../.github/workflows/bsi-ubs-hebrew.yml) verifies the exact pinned sources, runs all audits, regenerates both committed JSON datasets, and compares them deterministically. It operates in **read-only mode** after the validated source snapshot is committed.

The original source annotations and original WLC IDs are never rewritten. The next appropriate step is **edition-aware lexical reconciliation with an editorially validated sense policy**, not assuming numeric `LEXID` equality is a semantic guarantee.
