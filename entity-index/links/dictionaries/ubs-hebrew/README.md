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
