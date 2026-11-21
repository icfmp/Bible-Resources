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

The pinned WLC source and UBS Hebrew 0.9.4 confirm **10,794 additional
entry-only links** beyond the conservative four-field lookup. The word-aware
path is deliberately **not** an alias from unsuffixed Strong to suffixed
Strong: such a rule could conflate homonyms.

A link is permitted only when **all** of the following hold for an original
MACULA WLC source word:

1. Its ordinary exact source `sdbh`/Strong lookup has no UBS entry.
2. Its original source class is `noun`, `verb`, `adj`, `adv`, or `num`.
3. Its exact NFC lemma matches UBS **or**, for original WLC classes
   `verb`, `noun`, `adj`, or `adv`, the consonants match after removing only
   Hebrew vowel/cantillation marks, always **preserving shin versus sin dots**.
   Numerals and grammatical classes are never matched by this fallback.
4. Its H/A numeric Strong family plus the relevant lemma form identify
   **exactly one UBS headword**. If multiple UBS entries match the same
   consonantal form, the homograph remains unresolved.
5. Its **original complete MACULA word ID** is retained; source lemma,
   Strong code, and language must also match at lookup.

The verb-only orthographic step added **2,895** entries beyond the prior
7,588 exact-NFC lemma matches. Examples from original WLC words and pinned UBS
headwords include `יָלַד` → `ילד` (H3205), `חָטָא` → `חטא` (H2398)
and `זָכַר` → `זכר` (H2142). Consonant identity alone is **never**
considered sufficient: the original word ID, Hebrew/Aramaic Strong numeric
family, original WLC class `verb` and a unique UBS candidate must all agree.
Shin and sin marks remain meaningful, and multiple matching UBS headwords
are explicitly rejected. The added link is **entry-only**; no original
`sdbh` is translated or assumed to preserve its sense between editions.

The full-source [orthography audit](audit_orthography_gaps.py) identified
12,387 originally unresolved selected lexical-class occurrences. In addition
to the 2,895 verb corrections, **311** nouns, adjectives and adverbs with a
unique matching consonantal UBS headword and independent same-language Strong
family can now resolve to **entry-only** matches. The **183** original
same-consonant ambiguous candidates still remain deliberately unresolved.
There are now **9,181** unresolved selected lexical-class occurrences, including
8,156 for which the UBS 0.9.4 dictionary has no matching Strong family
(e.g., `כֹּל` H3605).

The new `lookup_word(index, word_id, sdbh, strongnumberx, lang, lemma)`
accepts that original word identity and returns **entry-only** evidence
(`sense_ids=[]`). It rejects mismatched original source fields instead of
silently picking a different entry. The existing four-argument
`lookup(index, sdbh, strongnumberx, lang)` stays unchanged and conservative
for callers that do not have WLC word IDs.

| Measure | Generic exact-source path | Original-word-aware path |
| --- | ---: | ---: |
| WLC occurrences with a candidate UBS headword | 257,038 | **267,832** |
| Additional unique-source headword links | — | **10,794** |
| WLC occurrences with Strong-corroborated SDBH sense IDs | 30,492 | **30,492** |
| Selected lexical-class occurrences with an UBS headword | 228,705 | **239,499** |
| Selected lexical-class coverage | 91.97% | **96.31%** |

Both paths remain pinned to the **same unmodified UBS and MACULA editions**.
The word-anchored path is an opt-in query using a frozen original MACULA
word ID; it cannot safely be substituted by a general Strong-prefix lookup.
No contextual sense is inferred, no original `sdbh` is rewritten, and
dictionary prose is unchanged.

The generator now stores `by_macula_word` plus
`coverage_with_word_ids` in [index.json](index.json); the
[full original-corpus CI](../../../../.github/workflows/bsi-ubs-hebrew.yml)
rebuilds both and verifies **10,794** new links and **267,832**
word-aware candidates. [test_word_anchored.py](test_word_anchored.py)
tests source identity isolation, H/A separation, disambiguation of entries
with *different* exact lemmas inside one Strong family, rejection of identical
homograph and same-consonant entries, nonverb class exclusions, and prevention
of cross-edition `sdbh` collisions.

## Source sense owner as independent headword evidence

A second source-anchored, **entry-only** recovery route identifies **16
additional WLC occurrences** that were unresolved by exact/normalized Strong
and lemma matching. It requires *all* of the following:

1. Original WLC word ID and exact original source fields are preserved.
2. A valid original 15-digit MACULA `sdbh` ID is **actually owned by one
   UBS 0.9.4 headword**.
3. The owning UBS entry has exactly the same **NFC-vocalized original lemma**
   as the MACULA source token.
4. The matching headword is **unique among all entries with that lemma and
   same H/A language**. No duplicate homograph and no H/A crossover.

Because the `sdbh` sense inventories diverge between editions, **the
original source sense ID is never transferred as a contextual sense** under
this new rule. It confirms only a dictionary headword.

The pinned full-corpus result changes **10,794** to **10,810** additional
word-anchored entry links (total **267,848** original WLC tokens linked).
For selected original lexical classes, **239,515 / 248,680 = 96.315%**
linked, and the edition-attested coverage becomes **239,515 / 242,726 =
98.677%**, with **3,211** occurrences still unresolved inside the edition's
indexed headword scope. All **5,954** inventory-unattested occurrences remain
separately excluded from that specific denominator only.

This is an incremental source-correlated identity check, **not** a claim that
the remaining entries sharing a lemma under different Strong numbers are
automatically equivalent. They remain flagged for independent review.

## Independent source-ID plus unique consonantal headword

Extending the strict source-ID-owner lookup to vocalization-only differences,
with the original same-language Hebrew consonants (shin/sin dots preserved)
and a unique matching UBS headword, recovered **2 additional original WLC
entry-only links**. This is separate from the 16 exact-lemma corroborations:
**10,812** extra source-word entries are now available, and **267,850**
original WLC tokens have a linked UBS headword candidate.

The original lexical-class coverage is **239,517 / 248,680 = 96.315%**,
and the edition-indexed-headword scope covers **239,517 / 242,726 =
98.678%**, leaving **3,209** in-scope lexical occurrences unresolved.
The excluded headword-inventory nonattestations remain **5,954**.
These two new links do **not** introduce any new contextual sense IDs.

Original source words, original SDBH IDs and UBS dictionary entries remain
unaltered. All same-consonant homographs, mismatched languages and ambiguous
source-ID owners are rejected. The absence of corroboration is **not**
treated as permission to guess.

## Coverage within the attested headword inventory (UBS 0.9.4)

The original WLC denominator must remain available, but an edition-specific
crosswalk should not be penalized for a headword **not identifiable anywhere
in this dictionary edition**. The complete pinned 7,943-entry UBS EN/FR
headword inventory was compared against every one of the 9,181 currently
unresolved WLC lexical-class occurrences—not just their Strong identifiers.

For this calculation, a source occurrence is considered **outside the
verifiable indexed UBS headword scope** only if all three checks fail:

1. The original same-language H/A numeric Strong family does not occur in
   any UBS 0.9.4 headword.
2. The source's exact NFC original lemma does not occur among *any* UBS
   headwords, including entries indexed under another Strong number.
3. The source's Hebrew consonants do not match any UBS headword after
   removing vowel/cantillation signs **while preserving shin/sin dots**.

This is **an operational headword-inventory test**, not a claim that the
word or its meaning cannot occur in the prose of a dictionary definition,
under a more remote orthographic variant or in a different edition. No
entry is invented or omitted from the original source corpus.

| Outcome on still-unresolved WLC lexical occurrences | Occurrences |
| --- | ---: |
| No compatible UBS Strong family or indexed headword spelling | **5,954** |
| Indexed headword evidence under a *different* Strong number | 2,202 |
| Same Strong family exists; original lexical identity unresolved | 1,023 |
| Unreadable or complex source code | 2 |
| **Total unresolved on the original corpus** | **9,181** |

In particular, **5,412** unmatched Hebrew occurrences of `כֹּל`
(H3605) have neither H3605 nor a matching indexed UBS Hebrew headword
in this pinned edition. Contrast `אַל`, `כֹּה`, and `עוֹד`:
their source Strong family is absent, but *another* UBS headword
shares the same consonantal spelling. They are **retained for review**
rather than declared absent. The 2,202 cross-Strong headword candidates
must never be silently treated as equivalent entries.

### Two denominators, explicitly separated

| Metric for MACULA classes noun/verb/adj/adv/num | Occurrences |
| --- | ---: |
| Original source corpus | **248,680** |
| UBS-linked WLC occurrences, unchanged | **239,499** |
| Not attested in UBS's indexed headword inventory under checked criteria | **5,954** |
| UBS-indexed-headword-scope denominator | **242,726** |
| Still unresolved **within this scope** | **3,227** |
| Full-source lexical coverage (retained) | **96.308%** |
| **UBS indexed-headword-scope coverage** | **98.671%** |

The generated index retains `coverage` (all original WLC occurrences),
`coverage_with_word_ids` (all word-anchored links), and adds
`coverage_scope` (this edition-specific denominator and explicit exclusion
criteria). The reproducible [scope audit](audit_dictionary_scope.py)
provides the top original word/Strong examples and per-class diagnostics;
[test_dictionary_scope.py](test_dictionary_scope.py) guards against
mistaking an alternate Strong for dictionary absence. The CI checks the
complete count conservation before accepting the generated snapshot.

## UBS-published alternate lemmas: edition-aware reconciliation

The exact pinned UBS Hebrew 0.9.4 English source has **1,041 headword
entries with source-authored `AlternateLemmas`**. These editorial forms
are preferable to guessing our own spelling variants.

The source-word-anchored crosswalk now accepts a published alternate lemma
only when its NFC spelling equals the **unchanged original MACULA lemma**,
the original H/A numeric Strong family agrees, and the match identifies
**exactly one UBS headword** in that family. Contextual sense IDs are never
inferred; existing exact links always take priority. Ambiguous aliases
remain unresolved. The same original WLC word-ID and original source
fields remain mandatory at lookup.

| Word-aware evidence type | New-source-word occurrence count |
| --- | ---: |
| Exact UBS headword lemma + Strong numeric family | 7,588 |
| UBS-published alternate lemma + Strong numeric family | **610** |
| Same-language consonants + Strong family, verbs | 2,881 |
| Same-language consonants + Strong family, nonverbs | 295 |
| Exact lemma + original SDBH owner | 16 |
| Same-language consonants + original SDBH owner | 2 |
| **Total source-word-anchored additional entry-only links** | **11,392** |

The alternate-lemma route accounts for **580 net new linked WLC lexical-class
occurrences** beyond the previous snapshot: 610 alternate-lemma successes
include 30 formerly linked through consonantal-only fallback.

### Updated inventory-attested denominator

The source-attested UBS indexed-headword inventory used to define the
**scope denominator** now includes *all UBS-published `AlternateLemmas`*
alongside main headword `Lemma`. That avoids declaring 21 original WLC
occurrences absent from UBS merely because the dictionary listed them under
an alternate spelling.

| Pinned source metric | Occurrences |
| --- | ---: |
| All five original WLC lexical classes | **248,680** |
| UBS headwords linked in source-word-aware lookup | **240,097** |
| Outside UBS headword inventory (no Strong family, canonical **or alternate** lemma, or matching Hebrew consonants) | **5,933** |
| UBS indexed-headword denominator | **242,747** |
| Still unresolved inside indexed-headword scope | **2,650** |
| Complete original lexical corpus coverage | **96.549%** |
| **UBS indexed-headword-scope coverage** | **98.908%** |

The original WLC corpus total and the 5,933 omitted-from-scope occurrence
records remain preserved. The scope metric reports edition-specific
*indexed-headword attestation*, **not** an absolute claim that missing
words or meanings never occur in definitions or another edition.
This section supersedes earlier numerical status snapshots in this README;
those historical snapshots are retained to document how the index evolved.

## Additional editorial-alias owner corroboration

A source-word-anchored cross-Strong lookup now checks whether a full
original MACULA `sdbh` identifier is owned by a *unique* UBS headword
whose **source-published `AlternateLemmas`** includes the exact NFC source
lemma, with matching H/A language. This requires both original UBS editor
attestation and source-ID ownership; an alternate spelling by itself is
not sufficient to bridge different Strong numbers.

The pinned corpus yields **1 additional entry-only link** under this rule.
No contextual sense link is inferred and prior matches are unchanged.

- Original WLC linked headword tokens: **268,431**.
- Selected lexical-class linked tokens: **240,098 / 248,680**.
- Edition-attested headword coverage: **240,098 / 242,747 =
  98.909%**, leaving **2,649** in scope.
- Outside verifiable edition headword scope: **5,933**, unchanged.

The source and dictionary texts are unchanged; homograph collisions,
unknown source IDs, and different H/A language are rejected.

## Version 1.0 acceptance: finish families, not source word occurrences

The *edition-specific indexed headword* scope is already at **98.909%**;
this is not an argument for guessing the remaining identities. A releasable
lexical bridge v1.0 requires five distinct gates:

1. **Every** unresolved original lexical occurrence is grouped under a
   reproducible language + NFC lemma + **original full Strong code** family,
   with original word ID, verse witness, counts and a source-grounded reason.
2. Every family has an explicit **editorial outcome**: accepted verified
   entry, genuinely absent from the pinned UBS indexed-headword inventory
   under documented checks, unresolved ambiguous, incompatible source
   identity, or specific source/index error requiring repair.
3. No unsubstantiated headword or contextual sense links. Zero **known**
   incorrect retained links; do not interpret source-ID equality as sense
   equivalence without independent corroboration.
4. Source editions and hashes are pinned, all generated data and counts are
   reproducible, and regression CI passes.
5. The original corpus coverage and the **separate** UBS edition headword
   scope metric are both retained: never inflate coverage by deleting source
   words or silently expanding exclusions.

### Machine triage baseline — not editorial sign-off

The complete [lexical family register](family_register.json), reproducibly
generated by [build_family_register.py](build_family_register.py), classifies
every original WLC noun/verb/adjective/adverb/numeral still unlinked after
the pinned UBS 0.9.4 dictionary and MACULA WLC word lookup.

| Evidence-based machine status | Families | Original occurrences |
| --- | ---: | ---: |
| No indexed headword found under stated UBS source checks | **5** | **5,933** |
| UBS has same exact main/alternate lemma but different Strong | **46** | **205** |
| UBS has same consonants but different Strong | **27** | **2,015** |
| UBS has same Strong numeric family, but entry is unresolved | **122** | **427** |
| Invalid or unsupported original source Strong syntax | **2** | **2** |
| **All unresolved original lexical families** | **202** | **8,582** |

Within the edition's attested headword scope, there are only **197
families / 2,649 original occurrences**, not 2,649 separate review cases.
Five families / 5,933 occurrences are excluded **only** from that narrower
scope, with explicit absence criteria, and remain in all original totals.

The three source-family hotspots are original `אַל` H0408 (**726**),
`כֹּה` H3541 (**577**) and `עוֹד` H5750 (**488**) — **1,791**
occurrences combined. They have similar consonantal entries in UBS
under another Strong family, **not verified lexical equivalences**.
Their original spelling, meaning, language and UBS dictionary entry
identities must be reviewed before authorizing an indexed link. Another
significant group is original `קׇרְבָּן` H7133 (**80**), with more than
one UBS headword in the same Strong family: do not pick a homograph.

**Current editorial validation:** 0 of the 202 machine-triaged families
has been marked as independently editorially accepted in this register.
That does *not* invalidate already linked words; it states that this
new unresolved-family worklist is a queue, not a claim to have manually
verified every unresolved lexical decision. The version 1.0 label is
**not yet earned**.

The register's source identifiers and candidate UBS IDs are audit
evidence, not approved correspondences. To proceed efficiently, review
distinct lexical **families in descending occurrence impact**, record
the resolution and evidence for the entire family, and batch-apply
only independently verified generic mapping rules with regression tests.
Classified-but-ambiguous and genuinely unattested families may remain
unlinked after a documented editorial decision; 100% lookup coverage
is neither necessary nor an acceptance gate.

## Source integrity and test workflow

- [build_index.py](build_index.py) produces `index.json`, preserving `by_sdbh` and `by_strong`, adding `by_entry_strong_family` for corroboration and retaining full coverage statistics. The generated index never contains dictionary definitions.
- [audit_direct_sense_fidelity.py](audit_direct_sense_fidelity.py) measures 165,214 raw equal-ID overlaps against independent MACULA/UBS lemmas and Strong identities.
- [audit_unmatched.py](audit_unmatched.py) categorizes unresolved original rows; [audit_variants.py](audit_variants.py) reports source morphology and lexical-class coverage.
- [audit_lexical_gaps.py](audit_lexical_gaps.py) groups unresolved lexical occurrences by original language/lemma; [audit_top_lemmas.py](audit_top_lemmas.py) examines frequent problem families.
- [audit_strong_reconciliation.py](audit_strong_reconciliation.py) reconstructs the **review-only** candidate report. Its original word-ID witnesses allow review without inventing entries.
- [test_index.py](test_index.py), [test_lexical_gaps.py](test_lexical_gaps.py), [test_strong_reconciliation.py](test_strong_reconciliation.py), [test_word_anchored.py](test_word_anchored.py), and [test_dictionary_scope.py](test_dictionary_scope.py) include offline synthetic regression tests.
- The [GitHub Actions workflow](../../../../.github/workflows/bsi-ubs-hebrew.yml) verifies the exact pinned sources, runs all audits, regenerates both committed JSON datasets, and compares them deterministically. It operates in **read-only mode** after the validated source snapshot is committed.

The original source annotations and original WLC IDs are never rewritten. The next appropriate step is **edition-aware lexical reconciliation with an editorially validated sense policy**, not assuming numeric `LEXID` equality is a semantic guarantee.

## V1 edition-scope editorial dispositions (2026-11-19)

[Source-keyed scope decisions](v1_scope_dispositions.json) independently record the
complete set of **five UBS 0.9.4 indexed-headword nonattestations** (5,933
original WLC occurrences). This accepts *only their exclusion from the edition
coverage denominator*, after the pinned Strong, exact main/alternate lemma and
consonant inventory tests; it does not assert semantic absence, rewrite the
MACULA tokens, or invent UBS entries. Re-evaluate when changing the UBS edition.

The same decision file explicitly **preserves both source composite Strong
strings** as unresolved original annotations (two source occurrences); splitting
or selecting a component has **not** been approved. The accompanying
`test_editorial_scope_dispositions.py` fails if a family key, original witness,
occurrence count, pinned source edition, or the lossless/no-lexical-link policy
changes. This is a separate manual disposition ledger: the generated
`family_register.json` remains a byte-reproducible *machine classification*
and its `families_with_editorial_decision=0` field must **not** be relabeled
as independent lexical editorial validation.

**No cross-Strong lexical identities or contextual meanings have been accepted**
by this scope-only review. The **197 in-scope families / 2,649 occurrences**
still need original source dictionary metadata and lexeme-level adjudication
under [#366](https://github.com/icfmp/Bible-Resources/issues/366).

## First lexical nonidentity decisions — three high-volume false homographs

The [source-keyed editorial rejection ledger](v1_lexical_nonidentity_dispositions.json)
records three **verified negative** decisions (1,791 original MACULA WLC
occurrences). None is a permitted cross-Strong link:

| Original WLC family | Occurrences | Rejected UBS 0.9.4 headword | Independent lexical reason |
| --- | ---: | --- | --- |
| Hebrew `אַל` H0408 | 726 | `000381000000000` `אֵל` H0410/H0411/A0412/H0415/H0416 | Original prohibitive *not* (Gen 13:8), UBS deity/noun/pronoun *god* |
| Hebrew `כֹּה` H3541 | 577 | `003248000000000` `כָּה` A3542 | Original Hebrew *thus/so* (Gen 15:5), UBS Aramaic *here* |
| Hebrew `עוֹד` H5750 | 488 | `005287000000000` `עוד` H5749 | Original temporal adverb *again/still* (Gen 4:25), UBS verb *testify/warn* |

These are **lexical non-equivalence judgments**, not a claim that the Hebrew
words are missing from all dictionaries. The parent algorithmic register's
same-consonant candidates and its coverage denominator are retained unchanged
for deterministic reproducibility. No original source word, Strong number,
verse or UBS entry is rewritten; none of these candidates is linked.

The [read-only verifier](verify_lexical_nonidentity.py), synthetic tests and
CI compare the exact original WLC word ID, reference, lemma, gloss, POS and
Strong fields against the pinned MACULA TSV and the complete actual UBS 0.9.4
headword lemma, Strong and POS metadata. It will reject an edition/source
revision or candidate-list change. The rationale remains an explicit human-
readable editorial judgment, not an unsafe automatic morphology rule.

**Initial three-family checkpoint:** these 3 large families were the first
rejected candidates (1,791 occurrences), before the subsequent reviewed batch.
The 5 edition-scope-only exclusions and 2 preserved composite Strong codes
are tracked separately. A rejected match does **not** create a dictionary
entry or semantic sense, and full-corpus linked coverage remains 240,098
out of 248,680. Publication remains subject to the v1 acceptance gate in
[#366](https://github.com/icfmp/Bible-Resources/issues/366).

### Further source-reviewed false homographs (batch 2)

Eight more **sole** UBS same-consonant candidates have been editorially
rejected with original language/word ID, contextual original English gloss,
morphology and exact UBS entry metadata, all checked in the same pinned-source
CI. They account for **18 additional original WLC occurrences**:

- `H עַל H5920` (6) and `H עַל H5921` (1): source *above/against* vs UBS
  `עֹל` H5923 *yoke*.
- `A אַל A0409` (4) and `H אֶל H0408` (1): source prohibitive *not* vs
  UBS `אֵל` *deity/pronoun*.
- `H נֶגֶד H5048` (2): spatial *opposite/suitable* vs UBS verbal
  `נגד` *tell/inform/flow*.
- `H עֹוד H5750` (2) and `A עוֹד A5751` (1): temporal *still* vs
  UBS verbal `עוד` H5749 *testify/warn/restore*.
- `H נָא H4995` (1): *raw* food vs UBS `נֹא` H4996,
  the named place *No/Thebes*.

**Total now explicitly dispositioned:** 11 rejected false-candidate families,
**1,809** occurrences. **Remaining in-scope without editorial disposition:
186 families / 840 occurrences**. The full lexical corpus denominator and
source-derived dictionary scope are intentionally unchanged; a rejected false
candidate is not a new UBS headword.

**Not rejected:** Hebrew `קָלָה` H7034 ('be degraded') may share an actual
meaning with the UBS `קלה` H7033 source entry, which includes a sense
'be degraded'. Similar Strong differences alone do not justify a negative
judgment. This remains for positive-identity review rather than a guessed link.

### Deliberate abstentions where one original Strong family has multiple UBS headwords

For the pinned UBS Hebrew 0.9.4 / MACULA WLC source pair, the
[v1 multiple-headword abstention ledger](v1_multi_headword_abstentions.json)
records **40 original lexical families / 275 source occurrences** where
**at least two distinct UBS headwords** occur in the *same* original-language
numeric Strong family. The ten largest families account for 241 occurrences,
including `קׇרְבָּן` H7133 (80), `זָנָה` H2181 (60), and
`תֹּולַעַת` H8438 (38).

The editorial *choice for this frozen v1 review* is to **retain these families
unlinked** instead of picking a first headword, conflating the distinct
dictionary records, or guessing contextual sense equivalence. This is a
documented **abstention**, not a declaration of lexical nonidentity, dictionary
absence, or a source correction. Future positive mappings must independently
review actual word context, candidate meaning and source edition identity.
Some families might be resolvable with sufficient evidence; the mere
presence of multiple candidates does not prove permanent ambiguity.

The [independent read-only verifier](verify_multi_headword_abstentions.py)
checks the exact 40 family keys, original occurrence counts, source word-ID /
reference / SDBH witnesses, candidate sets, original dictionary Strong
metadata, and pinned MACULA words. CI rejects source revision drift and any
attempt to convert an abstention into an approved entry or sense mapping.
The generated lexical family register remains an **algorithmic** baseline,
without falsely marking automatic triage as manual validation.

Together with 11 independently rejected false-homograph candidates (1,809
occurrences), this establishes **51 explicitly recorded conservative v1
dispositions / 2,084 in-scope source occurrences**. The **remaining
146 families / 565 occurrences** need their own evidence-based editorial
dispositions. All **240,098 / 248,680** verified original lexical source
links and the **98.909%** edition-attested headword coverage remain unchanged.
Do not label v1.0 as released without the separate approval gate in [#366](
https://github.com/icfmp/Bible-Resources/issues/366).

### Source-reviewed positive headword identities, without sense inference

The pinned-source [reviewed headword decision ledger](v1_reviewed_headword_dispositions.json)
records **5 additional original Aramaic families / 107 occurrences** whose
lexical identity was checked against the UBS dictionary article's distinct
meaning and the exact original word context. These are **editorial approvals
of a specific UBS headword identity only**, not yet generated WLC word links
and **not contextual UBS LEXID/SDBH sense approvals**.

| Original Aramaic MACULA family | Original occurrences | Reviewed UBS headword | Evidence |
| --- | ---: | --- | --- |
| `דָּנִיֵּאל` A1841 | 52 | `001695000000000` | Daniel, the book's principal character; UBS explicitly includes Dan 2:13–20 as one of several distinct name senses |
| `אֱנָשׁ` A0606 | 25 | `000553000000000` | Human/person in Ezra 4:11 and 6:11 |
| `יוֹם` A3118 | 16 | `002858000000000` | Day/time, including Ezra 4:15 and 4:19 |
| `בֵּלְשַׁאצַּר` A1113 | 7 | `001033000000000` | Babylonian king Belshazzar at Daniel 5:1 |
| `תּוֹר` A8450 | 7 | `007759000000000` | Cattle/bulls at Ezra 6:9, 6:17 (UBS Form 5); **not** the dove in the same combined dictionary entry |

The original source word ID, all three family sample references/SDBH IDs,
full Strong, language, original lexical class counts, candidate UBS MainId,
and exact pinned source revisions are recorded. Independent public UBS article
pages provide human-readable contextual corroboration. The
[read-only validator](verify_reviewed_headwords.py) then cross-checks
the recorded original word witnesses and the real UBS published main/alternate
headword forms in the **pinned** UBS 0.9.4 / MACULA source inputs, and CI
fails on any source or candidate drift.

The family-scoped approval does **not** make e.g. Aramaic A1841 a generic
Strong alias for every Hebrew H1841 entry, and it does **not** pick an UBS
sense for every word merely because the UBS entry combines several names or
meanings. A later separate, audited build change must add and regenerate
word-ID-specific entry-only links before these can count as linked coverage.

**Current v1 disposition count:** 11 source-backed false candidate rejections
(1,809 original occurrences) + 40 preserved multiple-headword ambiguities
(275) + these 5 reviewed positive headword identities (107) =
**56 / 197 in-scope families**, **2,191 occurrences with dispositions**.
The other **141 families / 458 occurrences** still require review. All
5 out-of-indexed-headword-scope families (5,933 original occurrences) and 2
composite source Strong codes are tracked separately. No source corpus counts,
generated crosswalk, actual word links or v1 publication status change in this
documentation-only positive batch.

### Second reviewed-entry batch: twelve Aramaic named entities (no universal aliases)

Twelve more source-identified lexical families have been reviewed against
original named referents in Ezra or Daniel and the matching UBS 0.9.4
published headword inventory. They contribute **47 original WLC occurrences**
to the **editorial headword-identification ledger**, without changing any
actual generated index link or contextual sense:

| Original Aramaic family | WLC occurrences | Original named referent |
| --- | ---: | --- |
| `יִשְׂרָאֵל` A3479 | 8 | Israel, Ezra 5:1 |
| `כּוֹרֶשׁ` A3567 | 8 | Cyrus, Ezra 5:13 |
| `יְהוּד` A3061 | 7 | Judah, Ezra 5:1 |
| `אַרְתַּחְשַׁשְׂתְּא` A0783a | 6 | Artaxerxes, Ezra 4:8 |
| `מָדַי` A4076 | 6 | Media, Ezra 6:2 |
| `רְחוּם` A7348a | 4 | Rehum, Ezra 4:8 |
| `זְכַרְיָה` A2148a | 2 | Zechariah, Ezra 5:1 |
| `חַגַּי` A2292a | 2 | Haggai, Ezra 5:1 |
| `מֹשֶׁה` A4873 | 1 | Moses, Ezra 6:18 |
| `יֵשׁוּעַ` A3443 | 1 | Jeshua, Ezra 5:2 |
| `יוֹצָדָק` A3136a | 1 | Jozadak, Ezra 5:2 |
| `חֲנַנְיָה` A2608a | 1 | Hananiah, Daniel 2:17 |

Every record in the existing [positive decision ledger](
v1_reviewed_headword_dispositions.json) stores its exact UBS `MainId`,
language + unchanged full original Strong / lemma, class counts, up to three
original WLC word-ID/reference/SDBH witnesses, a manual contextual
identity rationale, and the independently searchable dictionary index.
The read-only original-source verifier continues to check **all** entries,
now **17 families / 154 occurrences / 41 original witness IDs**, in pinned
UBS and MACULA snapshots. A name may be shared by multiple biblical figures;
only the *headword* is reviewed, not all individual sense/identity choices.

The reviewed ledger does not authorize transfer of MACULA SDBH identifiers
to UBS contextual senses, nor is it a universal Hebrew/Aramaic Strong alias.
No generated crosswalk coverage should be counted from an unimplemented
editorial approval.

**Cumulative distinct in-scope dispositions:** 11 negative candidate
rejections (1,809 occurrences), 40 multi-headword abstentions (275), and
17 positive headword identities (154) = **68/197 families / 2,238
occurrences**. Remaining **129 families / 411 occurrences**, excluding
the separately tracked 5 UBS edition-headword inventory exclusions.
An independent merge and explicit release gate are still required for v1.0.

### Original Hebrew grammatical segments carrying a compound Strong number

A distinct source-bound [ten-family morpheme decision ledger](
v1_source_morpheme_abstentions.json) records **27 original WLC word
occurrences** whose lexeme field is an **independent Hebrew preposition or
article**, not the UBS lexical noun/name headword that shares the
source annotation's inherited original Strong family.

- `לְ` with H3820b (11) and H5892b (2): preposition attached to a
  proper-name/compound context, **not** the named UBS headword.
- `הַ` with H0425b (3), H0329b (2), H3466a (2), H3873a (2),
  H5626a (1) and H6762a (1): definite article fragments inside lexical
  constructions, **not** full UBS place/name headwords.
- `בְּ` H1226a (2) and `מִן` H4675a (1): original location/source
  prepositions, **not** the inherited-Strong UBS content-word entries.

The original WLC source class can still say "noun" because the source
morpheme inherits a **composite or full lexical annotation**; these
editorial no-link decisions must not overwrite that source class, lemma,
source word ID, Strong, SDBH, or verse. A no-link is **not** a repair of
a potentially valid upstream segmentation convention.

The [source-pinned verifier](verify_source_morpheme_abstentions.py)
checks the original full family keys, 27 source counts, 19 original
word-ID/reference/SDBH witnesses, class counts, exact sole UBS MainId,
the original UBS Strong family, and the absence of equal standalone
consonantal headwords (preserving shin/sin distinctions). Synthetic
regressions forbid lexical approval or silent source rewriting. The
original `family_register.json` and generated `index.json`
remain byte-for-byte unchanged.

This is distinct from an unresolved true lexical homograph. It records
an explicit, reversible editorial **refusal to equate a grammatical
source segment with a full UBS dictionary entry**, never an invented
meaning or contextual sense.

If the other current lexical disposition batches are merged, the
combined in-scope tally becomes **86/197 families / 2,448 of 2,649
occurrences**, leaving **111 families / 201 occurrences** for separate
review. This conditional accounting is not a publication or merge claim.

### Third positive editorial batch: 17 source meaning-correlated headwords

An additional **17 original lexical families / 64 source occurrences**
have passed lexeme-level manual review against (a) exact source WLC
lemma/Strong/word-ID witnesses and passage context, and (b) actual
**pinned UBS Hebrew 0.9.4 published headword meanings**, including
distinct forms when one headword contains unrelated senses.

| Original lexical family | WLC occurrences | Reviewed UBS entry-level meaning | Representative source |
| --- | ---: | --- | --- |
| A `אֲרְיוֹךְ` 0746a | 5 | Arioch, royal guard captain | Dan 2:14 |
| A `מְלַל` 4449 | 5 | to speak | Dan 6:22 |
| A `עֲשַׂב` 6212a | 5 | vegetation | Dan 4:12 |
| A `אֱסוּר` 0613 | 3 | imprisonment | Ezra 7:26 |
| A `אִמַּר` 0563 | 3 | lamb | Ezra 6:9 |
| A `מִדָּה` 4061 and 4061a | 2 + 2 | tax | Ezra 4:20; 4:13 |
| A `מָזוֹן` 4203 | 2 | food | Dan 4:9 |
| A `עִדֹּוא` 5714b | 2 | Iddo, Zechariah's ancestor | Ezra 5:1 |
| H `מֹוסֵרָה` 4147a | 8 | bond / cord | Job 39:5 |
| H `שׁיח` 7817a | 5 | to be in distress | Ps 42:6 |
| H `רָפָה` 7498b | 4 | ancestor Raphah | 2 Sam 21:16 |
| H `נֵרִיָהוּ` 5374a | 3 | Neriah, father of Baruch | Jer 36:14 |
| H `זַעֲוָה` 2189 | 7 | horror | Deut 28:25 |
| H `אָשֵׁד` 0798 | 4 | slope | Deut 3:17 |
| H `נָבַב` 5014a | 2 | foolish / empty-headed | Job 11:12 |
| H `חַטָּאָה` 2402 | 2 | sin | Exod 34:7 |

The [existing positive editorial ledger](v1_reviewed_headword_dispositions.json)
now records **34 distinct headword-identified families / 218 original
lexical occurrences / 86 original word witnesses**. Every entry remains
a source-pinned, **headword-only** decision; no WLC word link is
actually added to the generated `index.json`, and no contextual UBS
LEXID or old MACULA SDBH is transferred.

The [read-only validator](verify_reviewed_headwords.py) is now generic
across three original machine statuses: exact UBS headword lemma under
different Strong, same-consonant candidate under different Strong, and
a unique UBS candidate in the original numeric Strong family. It
requires the actual pinned UBS headword to contain an expressly
recorded short English lexical gloss as independent meaning evidence,
and rechecks exact original MACULA WLC word IDs, references, class
counts and all source revision pins. The *gloss* identifies supporting
published lexical evidence, **not an assigned contextual sense**.
Regression tests reject semantic drift, wrong Hebrew consonants or
language/Strong matches, and any silent source/sense edit.

**Cumulative v1 review after this batch**, including independent
negative and abstention dispositions: **103 of 197 in-scope lexical
families / 2,512 of 2,649 original occurrences**. The **94 remaining
families / 137 occurrences** still require their own source review
before the explicit v1.0 approval gate. Source corpus and generated
index coverage are unchanged.

### Third source-verified lexical batch: source-English and UBS meaning corroboration

A further **22 original lexical families / 30 WLC occurrences** are accepted
as UBS **headword-only** identities using independently retrieved, immutable
original MACULA WLC word witnesses (original verse, source English where
recorded, NFC lemma, complete Strong, SDBH) and a **verbatim published UBS
lexical gloss** under the exact candidate headword.

Examples include:

- Hebrew קָלָה H7034 (6 original words): original Deut 25:3 **degraded**,
  UBS published gloss *to be degraded* in its second verb form — not a
  conjectural connection to the separate *roast/burn* meaning.
- Hebrew נַחֲלָה H5158a (2): source Wadi of Egypt at Ezek 47:19,
  UBS *wadi*; Hebrew צֹר H6697a (2): source *flint* in Josh 5:2,
  UBS *rock* / *blade* within the same headword.
- Hebrew שֹׁוקֵק H8264a (2): the *longing* soul of Ps 107:9,
  UBS *to be thirsty*.
- Hebrew handbreadth (2 source families), forest, furrow, terror,
  awakening, slaughter, merchants and Calno/Calneh, together with
  *broken* in Prov 25:19 and Isa 24:19.
- Aramaic Ecbatana, discernment, sin-offering, finding shade, the
  kor capacity measure and righteousness.

Each positive record remains **a judgment about a UBS headword**, never a
word-to-contextual-sense assignment. The UBS entry can contain several
English glosses or senses: a matching gloss confirms the documented lexical
review rationale but does not assign its source \`LEXID\` to every WLC word.

The existing [source-verified positive ledger](
v1_reviewed_headword_dispositions.json) and generic
[read-only source verifier](verify_reviewed_headwords.py) now check
**56 headword decisions / 248 source occurrences / 113 WLC word-ID
witnesses**. The new witness-English field, where actually present in
the pinned original lowfat chapter, is checked against the independent
original MACULA TSV in CI. A missing or changed UBS published gloss also
fails source validation.

This does **not** modify original MACULA/UBS text, original word IDs,
Strong/SDBH, generated index links, nor contextual sense inventories.
Full-source linked lexical coverage remains **240,098/248,680**
and the edition-attested-headword metric remains **98.909%** until
a separate verified link-generation step.

With previous source-reviewed dispositions, this batch brings the tracked
in-scope total to **125/197 lexical families / 2,542 of 2,649 original
occurrences**. **72 families / 107 occurrences** still need resolution,
including two preserved composite Strong annotations tracked as source
syntax cases. The UBS v1.0 release remains explicitly unapproved.

### Fourth source-review batch: 15 false single-headword candidates

The frozen original MACULA WLC lowfat words were independently inspected
for 15 more single-candidate UBS false matches: **38 original occurrences**.
These new negative lexical decisions cover exact original source word ID,
reference, language, full Strong, lemma, class, original POS, English (including
the deliberately empty original field when unannotated), and original SDBH,
as well as UBS exact MainId, lemma, Strong, original POS and a **verbatim
attested UBS gloss**.

The distinctions are editorial, not automatic rules for rejecting all
cross-Strong or same-Strong links:

- **Different lexical referents:** H שָׁתַן H8366a (6), original *one
  urinating* versus UBS source headword *male*; H לַיִשׁ H3919a (4),
  original city Laish in Judges 18, versus UBS *Laishah*; H רִמּוֹן
  H7417b (3), the deity in 2 Kings 5:18, versus the UBS settlement
  *Rimmono*.
- **Original components of larger names or locations:** H גּוֹי H2800a
  (3, Haggoyim within Harosheth-Haggoyim); H עֵמֶק H0425b (3,
  *valley* of Elah, not the Elah noun/name); H שְׁכֶם H4026b (3,
  *Shechem* in Tower of Shechem, not *tower*); H אָב H2361a (2,
  *Abi* title following Huram, not Huram himself); H שַׁעַר H3466a
  (2, Gate component in the Jeshanah Gate); H שְׁלִישִׁי H5697a
  (2, second source component of Eglath-Shelishiyah); H עֵמֶק H7104a
  (1, Emek component of Emek-Keziz).
- **Distinct lexical word and UBS meaning:** H אֶל H0413 (2),
  grammatical negative/preposition versus UBS divine being *god*;
  H בּוֹא H3820b (2), source *entrance* versus UBS *heart*;
  H קְוֵא / קֹוֶה H6961a (2+2), geographic *Kue* versus UBS
  *measuring line*; H יַעְרָה H3295a (1), actual Jonathan
  *honeycomb* versus the personal-name UBS *Jaarah*.

The existing [negative candidate ledger](v1_lexical_nonidentity_dispositions.json)
and [read-only pinned-source verifier](verify_lexical_nonidentity.py) are
extended rather than introducing a second negative-match algorithm.
A positive semantic mapping for an entire multiword construction would need
a separately documented, source-span-aware index; individual original-word
components are never silently promoted to an entire UBS name/headword.
The original Macula and UBS data remain untouched; no contextual senses
or new dictionary word links are inferred.

**After this batch:** negative decisions are **26 families / 1,847
occurrences**. Together with 48 previously reviewed multi-headword
abstentions (458), 10 grammatical segment nonlinks (27), and 56
positive headword-only identities (248), this is **140/197 in-scope
families / 2,580 of 2,649 original occurrences dispositioned**.
**57 families / 69 original occurrences** remain (including two
preserved composite source Strong annotations). The generated
word-linked index and UBS edition-scope metrics remain unchanged.

### Fifth source-backed lexical review batch: eleven additional positive UBS headwords

**11 more original WLC families / 12 original source occurrences** have a
specific, independently supported UBS **headword-only** identity based on
the pinned MACULA lowfat original word witness plus an exact published UBS
English lexical gloss. These include:

- Hebrew צַר H6887 (two words), *too small/cramped* in 2 Kings 6:1,
  UBS *to be narrow*.
- Hebrew גֵּישָׁן H1529, the named Geshan in 1 Chronicles 2:47,
  UBS *Geshan*; רָפָה H7498a, the named Raphah in 1 Chronicles 8:37,
  UBS *Raphah*; קָטָן H6997a, *Haqqatan* in Ezra 8:12,
  UBS *Hakkatan*.
- Hebrew אָדַשׁ H1759, the threshing in Isaiah 28:28, UBS *to thresh*;
  הֲנָפָה H5130b, sifting in Isaiah 30:28, UBS *to sift*.
- Hebrew נָגִיד H5048, noble words in Proverbs 8:6, UBS *noble words*;
  סָכַר H7936a, hired counsellors at Ezra 4:5, UBS *to hire*;
  סָלֵק H5559a, ascent in Psalm 139:8, UBS *to ascend*.
- Hebrew צָרַר H6862, *distress* in Lamentations 1:20, UBS
  *distress*; צרר H6696a, hostility toward foes in Exodus 23:22,
  UBS *to attack*.

The existing positive ledger is still independently verified by the
same source-pinned UBS/MACULA read-only validator; this increment
raises the totals to **67 positive headword decisions / 260 WLC
occurrences / 125 pinned original word-ID witnesses**. For every new
decision the exact first original WLC English field is compared against
the pinned independent source TSV; all recorded UBS glosses are checked
as members of the real source edition's lexical meanings.

**Important:** These are reviewed entry identities, **not actual
generated source-word-to-entry links**, original source rewrites, or
automatically assigned contextual LEXID senses. The generated index
remains unchanged. All family review outcomes together now account for
**151/197 in-scope families / 2,592 of 2,649 original WLC
occurrences**; **46 families / 57 occurrences** remain (two are source
composite Strong syntax cases separately preserved as unresolved).
No v1.0 publication approval has been given.

### Reproducible cross-ledger v1 disposition coverage (not a release gate)

The independent [v1 family disposition coverage report](
v1_disposition_coverage.json) is now generated by
[audit_v1_disposition_coverage.py](audit_v1_disposition_coverage.py).
Unlike the deterministic \`family_register.json\` machine triage, this report
counts separate **source-keyed manual editorial outcomes** across the
five existing edition/lexical ledgers, enforces **no duplicate family
decision** and conserves **every original source lexical occurrence**.
It rechecks original source edition revisions, exact family occurrence
counts and the authoritative frozen generated dictionary-index scope.

After the fifth reviewed lexical batch, the report distinguishes:

| Original-source distinction | Families | Original WLC occurrences |
| --- | ---: | ---: |
| UBS 0.9.4 indexed-headword scope exclusions | 5 | 5,933 |
| Lexically false sole candidates | 26 | 1,847 |
| Multiple-headword abstentions | 48 | 458 |
| Independent grammatical source-morpheme no-links | 10 | 27 |
| Source-verified positive *headword identities* | 67 | 260 |
| Composite original Strong strings retained unmodified | 2 | 2 |
| **Still lacking a distinct recorded editorial disposition** | **44** | **55** |
| **Original unresolved families and tokens** | **202** | **8,582** |

**Do not conflate two remaining-work metrics:**
- **151/197** in-scope families have an explicitly reviewed **lexical**
  decision; the other **46 / 57 occurrences** still lack a lexical
  disposition.
- Of those 46, **two original source composite-code families /
  two occurrences** already have a separate explicit source-preservation
  disposition. Therefore **44 families / 55 occurrences** are missing
  *any* recorded outcome. Neither means the 2 composite source codes
  can be rewritten, normalized or mapped without new independent evidence.

The full original **248,680** lexical observations still include
**240,098** actual existing UBS headword links and **8,582** unresolved
observations. All reviewed headword-positive decisions remain **editorial
records, not new generated original-word links**. The UBS edition-specific
headword index coverage stays **98.909%** and publication is **not
approved**. Every new ledger or edition change must update the
snapshot, then satisfy the read-only CI comparison against a fresh
rebuild from pinned original UBS and MACULA data. No coverage or
release percentage is fabricated from the editorial ledger count.

### Sixth source-reviewed batch: real lexical identities versus deceptive inherited headwords

Thirteen additional original WLC families, **14 original lexical occurrences**,
received deliberately limited editorial decisions after checking the original
passage and real UBS 0.9.4 headword meanings:

- **Nine false sole-candidate relationships / 10 occurrences:** palace
  **towers/strongholds** versus 'forsaken'; the two original **Beth-Haggan**
  word segments versus an unrelated **Beth-gilgal** location; **plenty**
  versus the person **Shiphi**; the Psalm 88 **leannoth** superscription
  versus **wormwood**; **Jeremoth** the person versus the towns named
  **Ramah**; a **robe** versus **measurement**; and two **Manahathite**
  clan-name forms versus **half**. These are *source-keyed rejections of the
  sole UBS candidate only*, not original corpus corrections.
- **Four independently corroborated UBS headword-only relationships /
  four occurrences:** **Tokhath** is also known as **Tikvah** (2 Chr
  34:22); **Ramathaim** belongs to the UBS **Ramah** entry that expressly
  names Ramathaim-Zophim (1 Sam 1:1); **Dragon Spring / En-Tannin**
  (Neh 2:13); and **Sheol**, world of the dead (Isa 7:11). The original
  source's pointed spelling, original word ID and source full Strong
  number are retained. None of these adjudications assigns a contextual
  UBS LEXID/SDBH sense or a universal Hebrew/Aramaic Strong alias.

The pinned UBS original candidate lemma, complete Strong/POS metadata
and published lexical gloss are checked against the actual source edition.
The independent original MACULA word ID, source verse, exact lemma, Strong,
class, English/POS witness and original SDBH are checked in the existing
read-only verifiers. For multi-occurrence families, the family decision
preserves all original unresolved tokens and does not silently create
word-to-headword mappings.

The source-conserving [v1 disposition coverage worklist](
v1_disposition_coverage.json) is regenerated from all five manual ledgers
without touching the original machine [family register](family_register.json)
or the pinned generated [index](index.json).

**After this batch:** **164/197 in-scope lexical families / 2,606/2,649
original occurrences** have distinct lexical dispositions. The two
original composite Strong-code families are separately preserved
losslessly. **31 families / 41 original occurrences** still have *no
disposition*. Reviewed positives are not actual new WLC links;
word-linked corpus coverage remains **240,098/248,680**, and the
UBS 0.9.4 edition-indexed-headword scope remains **98.909%**.
No v1.0 release or lexical-sense approval is claimed.

### Seventh source-reviewed batch: completion, boasting, desolation, and false sole candidates

Seven further original WLC lexical families, **seven original source-word
occurrences**, have separately supported v1 dispositions:

- **Four headword-only positive identities:** Aramaic `יצא` A3319 in
  Ezra 6:15 = *completed* (the UBS verb explicitly includes
  *to be completed*); Hebrew `יָמַר` H0559a in Isa 61:6 =
  *boast* (UBS `אמר` includes *to boast*); Hebrew `יָצַת`
  H5327a in Jer 2:15 = *destroyed* (UBS `נצה` includes
  *to be desolated*); and Hebrew `מָדוֹן` H4060 in
  2 Sam 21:20 = a man of unusually great stature (UBS `מִדָּה`
  includes *man of stature* / *giant*). No source spelling or
  sense identifier is changed.
- **Three false sole-candidate links kept unlinked:** the Egyptian
  magicians' *secret arts* `לְהָטִים` (Ex 7:11) versus a
  physical *blaze*; the original source *Ammi-* proper-name
  fragment `הוּא` (Song 6:12), annotated as a **suffix**,
  versus the personal pronoun *he*; and the first original
  *digging* segment `חֲפֹר` (Isa 2:20) versus the entire
  UBS lexical noun *mole rat*. In the last two cases, the original
  compound-family Strong annotation does not authorize a standalone
  constituent-to-whole lexeme link.

Possible **derived grammatical forms** (such as the grinders in
Ecclesiastes 12:3 versus the verb *to grind*) and **closely related
cultic terms** (such as incense altars versus burning) are **not**
negatively adjudicated merely because the English glosses differ:
they remain pending lexical-context review.

The existing independent pinned-source verifiers check original WLC
source words, languages, exact full Strong/SDBH, original English/POS,
and UBS canonical headword metadata and actual published glosses.
The generated index and original family machine report remain untouched.

**Current source-pinned disposition count:** **171 / 197 lexical
families**, representing **2,613 / 2,649 original in-scope occurrences**
with lexical outcomes. Both original composite Strong-code records
remain preserved without lexical decision; **24 source families /
34 occurrences** still lack a disposition. None of the newly
reviewed headword identities has been written into the generated
word index, and no contextual sense was inferred or v1.0 approved.

### Eighth batch: original names, attested lexical forms, and dissimilar proper places

The original source-fidelity review now records **eight more distinct
lexical families / nine WLC occurrences**:

- **Six entry-only headword identities:** the two *separately indexed*
  Aramaic components `יְגַר` and `שָׂהֲדוּ` of
  *Jegar-Sahadutha* (Gen 31:47); the Hebrew verbal `חָלָה`
  'grief' (Ps 77:11) corresponding to published UBS *to grieve*;
  `ירה` 'afraid' (Isa 44:8), explicitly supported by UBS
  *to be afraid*; `טֹחֲנֹות` 'grinders' (Eccl 12:3),
  a nominalized grinding agent with the same original Strong family
  as UBS *to grind*; and `אָשׁוּר` 'cypresses' (Ezek 27:6),
  supported by the UBS *cypress* tree term. Their original source
  lemma, source POS, full Strong number and SDBH identifier remain
  unchanged, even where the dictionary headword treats a nominalized
  form under a verbal entry. **No contextual lexical sense is inferred.**
- **Two false sole-candidate lexical links / three occurrences:**
  original *Eglath-Shelishiyah* in Isaiah 15:5 and Jeremiah 48:34
  is a Moabite place, not UBS *Eglah*, David's wife, nor an
  ordinary heifer; and the original Zuphite/Zophim ancestral
  designation in 1 Samuel 1:1 is not the UBS *field of Zophim*
  located in Moab (Num 23:14), nor the verb *to watch*.

The new positive and negative decisions remain keyed to the precise
original word-ID/reference/family, with original English and full
UBS 0.9.4 lexical evidence. The independent source-pinned checks and
full cross-ledger conservation audit reject any drift of original
candidate identities, source revision or lexical witness.

With this batch, **179 / 197 in-scope families** and
**2,622 / 2,649 original in-scope occurrences** have a lexical
disposition. **16 distinct source families / 25 occurrences** have
no disposition yet. The two original composite Strong-code annotations
remain separately preserved. Actual generated word links and the
UBS 0.9.4 indexed-headword coverage remain unchanged; the
version 1.0 publication and contextual sense assignment remain unapproved.

### Final 16 single-candidate families: documented abstention, not a guessed UBS link

The independent [v1 single-candidate abstention ledger](
v1_single_candidate_abstentions.json) now records an explicit, source-keyed,
**reversible no-link editorial decision for the last 16 in-scope source families
(25 original WLC occurrences)**. Although the machine classifier finds
exactly one UBS dictionary candidate for each, its Strong or orthographic
similarity alone does not establish atomic original lexeme identity.

The case-by-case decisions retain concrete uncertainty rather than
inventing links or arbitrarily declaring nonidentity. Representative
categories include:

- **Distinct or incompletely identified places:** original Rimmon
  settlement witnesses spanning Judah/Simeon and Zebulun versus the
  narrower UBS Rimmono Levite-town headword; Bamoth-Baal versus UBS
  Bamoth of the Exodus route.
- **Segmentation/granularity:** the first original word of the Bor
  Sirah proper name versus a single UBS full-compound place entry;
  a standalone animal-name constituent versus the complete
  *mole rat* entry; the original components of the cryptic
  Leb-Kamai name and of Ammi-nadib versus ordinary lexical headwords.
- **Related yet unproven derivational or semantic identities:**
  valuable gifts versus the verbal desiderative lexeme; the
  original garment-wearing form versus a UBS clothing noun;
  incense altars and sacrificial incense forms versus a UBS
  action noun for burning; helpless sufferers versus a proposed
  victim noun.
- **Original contextual conflicts:** a named individual Hesed
  versus a common-noun loyalty dictionary entry; a Joshua 9:4
  source verb with competing English and analytical glosses;
  the exact meaning and species of the Ezekiel 31 tree term.

For **each exact family**, the ledger records original NFC lemma, H/A
language, **unchanged full Strong code**, source word count, all pinned
sample word IDs/references/SDBH fields and source classes, original
first-word English and POS, the exact sole UBS MainId with original
lemma/Strong/POS and an actual original UBS published gloss, a distinct
uncertainty category and a substantive contextual rationale. The
[independent verifier](verify_single_candidate_abstentions.py) rechecks
these source witnesses in the frozen MACULA WLC TSV and the complete
UBS Hebrew 0.9.4 dictionary; synthetic regression tests and GitHub CI
forbid silently converting an abstention into lexical/sense approval.

A recorded abstention **is neither a proven negative equivalence nor a
verified positive headword identity**, and may be revisited on stronger
original-language evidence. It cannot create a generated link, inferred
contextual UBS LEXID/SDBH or a universal Strong alias.

**Source-conserved disposition checkpoint:**
- **All 202/202 original unresolved families have a recorded disposition**:
  5 indexed-UBS-edition scope exclusions, 2 preserved original composite
  Strong code annotations, and **195 other lexically dispositioned
  families**.
- All **197/197 in-scope families / 2,649 original occurrences** have
  an explicit outcome, but the two composite source-code families
  (2 occurrences) are **preservation-only**, not lexical identity sign-off.
  Thus **195 lexical dispositions / 2,647 occurrences**, plus
  2 separate lossless source-annotation dispositions.
- Positive source-backed UBS headword identities remain editorial
  evidence and have **not yet been promoted to generated WLC word links**.
  Original source lexical linking remains **240,098/248,680**
  and UBS edition-indexed headword scope **98.909%**.

**Do not close issue #366 or publish/approve UBS v1.0 on this worklist
alone.** Final acceptance still requires source-to-index link integration
for approved word-level cases, independent zero-known-incorrect-link
audit, full pinned regeneration/CI and owner editorial approval.

### Entry-only preview from explicitly witnessed original MACULA words

The v1 lexical audit now documents each original unresolved family, but its
**81 positive headword identities / 274 original lexical occurrences** are
editorial source decisions, not automatically generated word-level links.

The [source-witness anchor preview](reviewed_word_anchor_preview.json) adds an
**independent, nonpublished and reversible candidate layer** for only the
**139 original WLC word IDs explicitly enumerated** in the 81 positive
editorial records. It does **not** assume the other 135 occurrences share an
identical contextual lexical interpretation. The generated original
`index.json`, scope and original `family_register.json` are unchanged.

The [stage/verification script](stage_reviewed_word_anchors.py) uses the
published UBS 0.9.4 source revision, pinned MACULA WLC source revision and
the existing editorial identity verifier. It verifies every original word
ID, passage, lemma, full Strong, SDBH, source class, and the dictionary
headword source, checks each word is not already linked in the original
index, and proves that an entry-only lookup never returns contextual
sense IDs. CI compares the staged source-derived JSON with the committed
preview and refuses drift.

**No new lexical coverage is claimed by this preview**, and no runtime
application is required to consume it. Subsequent work should review the
remaining words individually, then explicitly apply only verified original
word-ID anchored links to a new generated index with full-regeneration
tests. No global Strong alias or original source correction is licensed.

### Exact WLC census for every positive editorial headword family

The [pinned original-word evidence report](positive_family_pending_original_words.json)
enumerates **all 274 original WLC lexical occurrences** across the 81
independently reviewed UBS headword families. It separates the **139 exact
word IDs** already in the nonpublished entry-only preview from **135 further
original source words** needing individual lexical review. Those 135 words
occur in just 20 families, principally Daniel (49), Aramaic human/person
(22) and day/time (13).

Every pending occurrence retains its **exact original WLC Unicode lemma**,
full Strong, original SDBH, word ID, verse/position, MACULA English, POS,
morphology and source lexical class. A [read-only generator](
audit_positive_family_unwitnessed.py) checks all family cardinalities and
previously witnessed word IDs against the pinned original MACULA TSV. The
existing UBS CI verifies the entire committed report is reproduced exactly,
and synthetic tests reject missing/modified WLC words and existing links.

This report **does not approve** any of the 135 pending words, does not
infer UBS contextual senses, and does not alter the immutable crosswalk
or original corpus. Any additional entries require independent word-specific
editorial evidence; a family-wide positive decision is not a licence to
assume all contexts mean the same thing.

### Individual WLC word-headword reviews beyond the first 139

The [additional editorial word ledger](v1_additional_word_headword_dispositions.json)
records **134 further original WLC word IDs** after checking each exact
source English, POS/morphology, passage, original full Strong and SDBH
against an independently published UBS headword meaning. The decisions
cover **19 families** and are headword-entry-only, not contextual sense IDs.

Every record preserves its original MACULA spelling and combining-mark order.
The [read-only verifier](verify_additional_word_headwords.py) checks the
135-word source census, exact complete original MACULA TSV evidence,
UBS pinned lexical glosses and original index nonlink status. CI fails
for altered WLC words, unsupported English meanings, dictionary drift,
existing-link collisions or fabricated senses.

The last original pending word in **2 Samuel 21:22**, Hebrew רָפָה
(MACULA English 'giant'), is **deliberately kept unlinked**. This
original source word need not refer to the named Raphah ancestor rather
than a giant/descendant. The UBS personal-name headword does not alone
resolve the contextual identity; we must not force this link.

The 134 newly reviewed words, together with the existing 139 exact
word-ID entries in the first preview, yield **273 staged headword-only
candidates**. Both independently verified overlays are still separate
from the frozen generated index.json. No original sources, SDBH, Strong,
UBS sense IDs or application code changed. Actual index regeneration and
explicit publication approval are separate future gates.

### Source-word-verified private v1 candidate index (not publication)

The [private candidate rebuild](build_private_reviewed_candidate.py) combines
exactly **273 individually reviewed MACULA WLC word IDs** from the two
independently source-checked entry-only overlays (139 + 134). It preserves
one deliberately unresolved word in 2 Samuel 21:22, never fabricates
contextual UBS lexical sense IDs, and does not modify original MACULA or
UBS data or the frozen, committed original `index.json`.

The builder independently checks each original source word's exact raw
Unicode lemma, full Strong, SDBH, verse and source class against the pinned
MACULA TSV, plus actual UBS headword membership; confirms no previous
lexical link is overwritten; then recomputes complete original WLC coverage
and the separately defined UBS edition-headword scope. It refuses unrelated
source drift, wrong counts, duplicate candidates and any changed legacy
lexical sense or Strong mapping.

The reviewed candidate is regenerated in pinned UBS CI and uploaded as
the separate GitHub Actions artifact
`bsi-ubs-v1-private-reviewed-word-candidate`. It is explicitly marked
**not approved or published** and is not added to public download catalogues.
Only the independently approved source-word entry anchors are considered;
no global Strong equivalences, original source changes or semantic
inferences are introduced.

### Attributed, reproducible v1.0 technical release candidate

The [v1.0 readiness record](V1_RELEASE_READINESS.md) is the publication
checklist for this **nonpublished** source-pinned crosswalk. The
[deterministic packaging script](package_reviewed_v1_candidate.py)
combines the previously full-corpus-verified 273-entry private candidate
with CC BY-SA 4.0 rights/changes notices, exact original UBS 0.9.4 and
MACULA WLC revision attributions, a per-file hash manifest and a ZIP SHA-256.
GitHub Actions uploads this only under
`bsi-ubs-hebrew-v1-technical-rc-NOT-PUBLISHED`; it is neither a GitHub
release nor an active application dictionary resource.

The package generator verifies the frozen 99.021% indexed-headword
scope, exact JSON SHA-256, 273 reviewed entry-only word identities,
unmodified source edition and all existing sense-link counts. It
rejects unsupported source editions, contextual sense additions,
truncated staged words and unauthorized publication status.

**Publication approval is separate from source verification and PR merge.**

### Final individually source-checked lexical uncertainties and v1.0-rc2

The first private v1.0-rc1 candidate (273 links, 99.021%) is retained
unchanged as a reproducible historical witness. A fresh, independent,
original-WLC audit of the last **25 single-headword-uncertain words plus
one original giant/Raphah word** identified **two** more defensible,
original-word-specific UBS headword correspondences. Exactly eight
other same-family WLC words were **already linked**; no general
Strong-family alias is created.

- **Joshua 19:13 Rimmon**, original `o060190130101` maps only that
  specific Zebulun place token to UBS **Rimmono**; southern towns and the
  Rock of Rimmon are separate and remain deliberately unlinked.
- **1 Samuel 17:39**, original `o090170390072` maps its source-attested
  verbal use 'tried/he undertook' to UBS **יאל**, H2974. Original lemma
  `אלה`, consonants/diacritics, Strong suffix and source word-ID remain
  untouched. No proposed source-text emendation is performed.

The [final review decisions](v1_final_word_specific_approvals.json),
[source-attestation audit](audit_final_lexical_uncertainties.py) and
[complete-source private rebuild](build_final_reviewed_candidate.py)
verify these two exact words, preserve all previous links, re-audit
**475,911** original WLC words and explicitly retain **24** residual
word-specific abstentions. The final 275-word private candidate,
[manifest](v1_final_candidate_manifest.json), and deterministic CC BY-SA
attributed **v1.0-rc2** ZIP are review artifacts **only**. The original
committed index remains unchanged.

Edition-specific indexed-headword scope: **240,373 / 242,747 = 99.022%**,
with **2,374** in-scope original lexical words unlinked (1,863 rejected
nonidentities, 458 multiple-headword ambiguity, 27 grammatical fragments,
23 single-candidate abstentions, 2 composite annotations and 1 Raphah
lexical identity). **5,933** additional original source tokens remain
outside UBS 0.9.4's attested indexed-headword inventory. These are not
2,374 known fixable errors. Headword coverage is not a contextual
semantic-accuracy metric; no contextual UBS sense ID is inferred.



## Bounded v1.1 semantic feasibility — no inferred sense changes

A one-pass, source-pinned v1.1 audit [documents the complete outcome](
V11_SEMANTIC_FEASIBILITY.md): **53,981** original WLC source words
without an accepted UBS sense have a *single UBS sense whose EN/FR source
reference cites their verse*, and the original verse has only one
source-verified WLC word of that UBS headword. These words span **1,768**
lexical entries, but **zero** are promoted to contextual meaning
decisions. The 233,190 original entry-only words are fully partitioned
into defensible citation candidates, collisions, missing or ambiguous
references and other unresolved source outcomes.

**Decision:** this is enough scale to justify an *independently
sample-validated semantic experiment*, but not enough to auto-assign
53,981 contextual LEXIDs. Avoid the known MACULA SDBH ↔ UBS 0.9.4
numeric-ID collision, preserve the source editions and ambiguity,
and leave the [published v1.0.0](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-hebrew-v1.0.0)
unchanged.
