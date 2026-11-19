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


## First source-reviewed Greek headword batch — three pronouns

The [original-word review ledger](v1_reviewed_pronoun_headwords.json)
selects the already source-audited pronoun headword identities
`σύ` (you), `ἐγώ` (I) and `οὗτος` (this/that). These are **word-ID-specific,
headword-only** decisions: they do not infer an Louw–Nida contextual meaning.

The independent [review builder](build_reviewed_pronoun_candidate.py)
re-audits the original **137,741** SBLGNT word records and all **5,938**
previously generated source-preview candidates against original UBS Greek
1.0 EN/FR. It requires the exact original word ID, source Greek lemma
under Unicode NFC equivalence, MACULA `class=pron`, source Strong and
morphology, and an original Louw–Nida code *within the same authentic
UBS headword*. Greek dictionary POS abbreviations `pprs.` and `pdem.`
are recognized as personal/demonstrative pronouns, without rewriting them
or pretending an absent dictionary POS tag is evidence of another class.

| Source-attested original Greek lexeme | Independently reviewed word-ID links |
| --- | ---: |
| `σύ` | **1,971** |
| `ἐγώ` | **2,156** |
| `οὗτος` | **906** |
| **Total original-word-only headword approvals** | **5,033** |

**905** of the 5,938 strict original lemma+LN candidates remain explicitly
**unapproved**. Additionally the original corpus has 3,249 lemma-only/no
common source LN words, 459 with no NFC-identical UBS 1.0 headword, and
five unsupported Strong structures, none of which are automatically linked.
Thus **133,123 / 137,741** original words have an existing source Strong
entry candidate or a first-batch reviewed individual word-ID headword
mapping; the extra **905** unapproved preview links are **not included**
in this editorially approved coverage. Original Strong-only sense
candidates and original historical indexed `index.json` remain unchanged.

The source-review pipeline records the exact 5,033 original word mappings
in the private regenerated
`bsi-ubs-greek-reviewed-pronoun-private-candidate.json` (Actions artifact,
NOT a release), verifies its SHA-256
`867d69186e718939ee55ef91403755240972a1e4c31ddc091e4974d1a524fda0`,
and rejects modified original lemmas, Strong values, LN codes, morphological
fields, source verses or original word IDs. Semantic sense choices remain
**0 newly inferred**. It has not been promoted to a public download or
integrated into the Bible application.

The next editorial batches are tracked in
[issue #396](https://github.com/icfmp/Bible-Resources/issues/396).

## Second source-reviewed Greek lexical headword batch — ten non-pronoun families

The separately source-verified [batch-2 decision ledger](v1_reviewed_families_batch2.json)
covers ten explicit original Greek lexical families: `πρῶτος`, `εἷς`,
`λέγω`, `ἐσθίω`, `εὐθύς`, `πολύς`, `μέγας`, `ὑπάρχω`,
`δείκνυμι`, and `πίμπλημι`. Their exact original
MACULA word IDs, unchanged Greek lemmas, original Strong annotations,
morphologies, references and original Louw–Nida witnesses are independently
rechecked against the pinned UBS EN/FR lexicon. UBS source POS
(`adjc.`/`verb`, including entries listing `advb.` and `adjc.`
together) must agree with each original MACULA lexical class.

The [private batch-2 builder](build_reviewed_families_batch2.py) uses
the full [905-word evidence register](audit_remaining_headwords.py) and
approves **only 577 additional original word-ID/headword identities**, without
creating a universal Strong alias or selecting any contextual lexical
sense. Together with the previously reviewed 5,033 source-word pronouns,
**5,610** additional original Greek words have individually reviewed
headword candidates. The original **128,090** Strong-based lexical
candidate words stay unchanged. Editorially reviewed headword coverage is
therefore **133,700 / 137,741 (97.066%)**; the remaining **328** strict
lemma+LN word previews remain unapproved. The separate 3,249 source
lemma-only/no attested UBS LN words, 459 without matching source UBS
headword, five composite Strong forms and original 224 multiply headed
Strong cases remain unresolved. These are not contextual-sense accuracy
figures.

CI separately checks complete source inventory, bilingual dictionary
parity, original word-ID-to-entry witnesses, POS alignment, zero modified
source annotations, zero invented contextual `LEXID`, and preservation of
the frozen `index.json`. The versioned source-reviewed result remains
an **expiring private GitHub Actions artifact, NOT a download or release**.

## Original εἰμί headword-only review without UBS lexical senses

The separately source-verified [εἰμί decision ledger](v1_reviewed_no_ln_headwords.json)
and [original-word builder](build_reviewed_no_ln_headwords.py) cover **2,031**
previously unlinked exact MACULA original word IDs with original lemma
`εἰμί` (NFC Greek equivalence), the original grammatical class `verb`,
real inflectional Strong annotations and morphologies, and an original
UBS v1.0 EN/FR bilingual-identical headword with source Strong `G2258`.
The original dictionary grammatical metadata labels it `verb` in English
and `verbe` in French. These source differences are deliberately preserved.

**This approves a lexical entry/headword, not an UBS contextual sense.**
The original UBS entry genuinely has zero `LEXMeanings` in both languages;
no contextual `LEXID`, original LN code or global Strong alias is
inferred. The 2,031 exact source word IDs are individually rechecked
against all 137,741 original SBLGNT tokens. The previous 5,610
original-word headword approvals and frozen original `index.json` remain
untouched.

The resulting source-reviewed **headword-only** coverage is
**135,731 / 137,741 (98.541%)**: 128,090 pre-existing Strong headword
candidates plus 7,641 individually reviewed word headwords. This must
not be represented as 98.541% contextual sense accuracy or a claim that
the original dictionary contains missing meanings. Remaining: 328
strict original lemma+LN previews still unapproved, 1,218 other original
lemma-only/no UBS LN words not linked, 459 without a canonically equal
UBS headword, five unsupported composite Strong words, and 224 already
multiply headed source cases left ambiguous. The original unmodified
historical index and every source Greek/Strong/morph/LN annotation are
still preserved.

The result is a **private, expiring Actions review artifact** only,
without a public download, SWORD release or Bible application integration.

## Third Greek headword review batch — 155 original words

The [third source-specific editorial ledger](v1_reviewed_families_batch3.json)
identifies **19** individually documented lexeme families and **155** original
MACULA SBLGNT word IDs from the exact [remaining-source register](audit_remaining_328.py).
The [batch-3 verifier](build_reviewed_families_batch3.py) rechecks their
exact UBS 1.0 bilingual Greek headword IDs, NFC-identical lemmas, independently
attested original UBS Louw–Nida codes, MACULA morphological classes and
all unchanged source Strong/verse/word witnesses. Source nouns, verbs and
adjectives must have compatible original UBS lexical part-of-speech labels.

The original 5,033 reviewed pronouns, 577 prior ordinary Greek headwords,
2,031 entry-only `εἰμί` source-word links, and the frozen original `index.json`
remain unchanged. The additional **155** make **7,796** reviewed source-word
headword approvals. Combined with the original 128,090 Strong-derived
headword candidates, coverage is **135,886 / 137,741** original Greek words;
**173** previously strict NFC+LN source preview words remain unapproved.
The 1,218 other lemma-only/no-LN, 459 no-exact-headword, five composite
Strong tokens, and 224 pre-existing multiple-headword ambiguities remain
outside this approval.

This is **lexical entry/headword identity only**, not contextual meaning
accuracy. No extra `LEXID` has been inferred, no original Strong or
source Greek text has been changed, and no Bible app or SWORD publication
has been performed. The CI-generated output is a temporary **private**
Actions artifact, not a released index.

## Fourth Greek lexical review batch — 138 source word IDs, seven deferred families

The [fourth explicit source-specific ledger](v1_reviewed_families_batch4.json)
and [source-word verifier](build_reviewed_families_batch4.py) review
**138 additional exact original SBLGNT word IDs in 101 lexical families**.
These families have matching NFC original Greek headwords, exact source
UBS v1.0 EN/FR Louw–Nida corroboration, compatible original MACULA and
UBS lexicographic classes (noun, verb, adjective, adverb, preposition,
conjunction), preserved nonzero original Strong witness and complete
original reference/morphology/word-ID evidence. No individual word gains a
contextual UBS `LEXID`, and no Strong number is globally aliased.

The separate ledger explicitly **defers 35 words in seven families**:
`τεσσεράκοντα` 22 and `ἐνενήκοντα` 4 (MACULA numeral vs UBS
`adjc.`), `ὅστις` 5 (MACULA pronoun vs UBS `prel.`),
`ὁ` 1 (MACULA determiner vs UBS `artc.`),
`ὁπότε` 1 (MACULA conjunction vs UBS `advb.`),
and `ἄμωμον` and `Ἀρνί` one each (source original Strong `0`).
These are **source-specific lexical classification and annotation
differences**, not missing Greek words. None is silently altered to
satisfy an artificial coverage target.

Source-reviewed new original-word headwords now total **7,934**, plus the
original unchanged **128,090** Strong-based candidate words: combined
**136,024 / 137,741** have lexical entry candidates. This is not
contextual-sense accuracy. The **35** strict candidates above, the other
1,218 lemma-only/no matching UBS LN, 459 no matching UBS headword and five
composite Strong cases remain outside the reviewed candidate. The original
224 multiple-headword entries are still explicitly ambiguous. The
historical `index.json`, both original dictionaries and all source
Strong, Greek, morphological and LN annotations remain unchanged.
All newer outputs remain **private, expiring Actions review artifacts**,
not published SWORD/Bible resources.

## Fifth Greek source-word lexical headword review — 1,218 lemma-only occurrences

The complete [original-source no-LN audit](audit_remaining_no_ln.py)
verifies all 137,741 pinned MACULA SBLGNT word IDs against the original
bilingual UBS Greek NT Dictionary 1.0. Among the original **3,249**
lexical lemma-only/no-common-UBS-Louw–Nida occurrences, **2,031** original
`εἰμί` word IDs were already separately reviewed as entry-only
headwords. The other **1,218** source word IDs belong to exactly eight
Greek lexical families:

| Original Greek lemma | Source words | Original UBS POS evidence |
| --- | ---: | --- |
| `ἑαυτοῦ` | 493 | `prfl.` reflexive pronoun |
| `σύ` | 445 | `pprs.` personal pronoun |
| `οὗτος` | 248 | `pdem.` demonstrative pronoun |
| `ἐγώ` | 17 | `pprs.` personal pronoun |
| `ῥέω` | 10 | English `verb`, French `verbe` |
| `ἄρχω` | 3 | English `verb`, French `verbe` |
| `εἷς` | 1 | `adjc.` |
| `προοράω` | 1 | English `verb`, French `verbe` |

The [eight-family explicit review ledger](v1_reviewed_no_ln_families_batch5.json)
and [original-word verifier](build_reviewed_no_ln_batch5.py) confirm
each source word ID, exact Greek NFC headword, unique UBS original
bilingual MainId, original source Strong, original morphology/reference,
part of speech and the **absence of a matching original lexical LN code**.
This supports **lexical headword identity only**, not a contextual meaning.
No UBS `LEXID` is chosen, no source LN or Strong is rewritten and no global
Strong alias is created. It is an explicitly distinct review decision
from the earlier LN-corroborated word-ID batches.

The resulting additional source-reviewed word-specific headwords total
**9,152**, alongside the original unchanged **128,090** Strong-derived
entry candidates: **137,242 / 137,741** original Greek words have
source-attested lexical entry candidates. The previous **35** explicitly
unapproved source-POS/Strong conflicts, **459** without an NFC-identical
UBS source headword and **five** unsupported composite Strong forms
remain unresolved (499 original source words). The existing 224
multiply headed Strong-based candidates remain ambiguous and are
not silently reduced to one entry.

This is **not lexical sense/context accuracy**, and does not imply
a new downloadable resource or a Bible app integration. The complete
source-reviewed overlay is built and independently verified in CI as
a **private, expiring Actions review artifact**, while historical
`index.json` and all original Greek/Strong/LN/morphological source
data stay byte-for-byte unchanged.

## Exact-source unresolved Greek lexical exceptions

The [independent original-token exception census](audit_final_exceptions.py)
rereads all 137,741 pinned SBLGNT original word IDs and both UBS Greek
Dictionary 1.0 language editions. It preserves full source witnesses
and does **not** change historical lexical maps or private source-reviewed
word-ID entries. Its final bounded original-source cases are:

| Original source disposition | Words | Editorial status |
| --- | ---: | --- |
| No NFC-identical UBS source lemma | **459** | No invented headword |
| Unsupported composite original Strong | **5** | Original compound code preserved |
| Original strict lemma+LN candidates with source POS/Strong conflict | **35** | Not automatically approved |
| Pre-existing multiple UBS headwords under one original Strong | **224** | All original candidates retained; not counted among the 499 unmatched |

The largest 459 truly no-exact-headword Greek source families are
`ἰδού` (200), `Ἰερουσαλήμ` (76), `ἱερόν` (30),
`ἴδε` (30), `ἕνεκεν` (20) and `περισσότερος` (15).
These may reflect missing dictionary entries, source lemma spelling
choices, or editorial distinctions; **none** should be blindly
redirected to a similarly spelled original UBS entry.

The five composite original Strong instances are
`ὑπερεκπερισσοῦ` (`5228+1537+4053`, three words),
`δισμυριάς` (`1417+3461`, one) and
`ἐκπερισσῶς` (`1537+4053`, one). The source components
are preserved exactly instead of treating one arbitrary component as
the original lexical identity.

The **224** previously matched-but-ambiguous original Greek words
mainly belong to `πόλις` (162, plus one `Πόλις`),
`ἐλεάω` (32), and `πάρειμι` (25).
Their source report retains every UBS `MainId`, original Greek lemma,
original Louw–Nida matches and original word ID. A further independent
per-word lexical-family decision is required before narrowing any of
these; the historic Strong-derived ambiguities are left unchanged.

The currently reviewed *headword identity* coverage remains
**137,242 / 137,741** original SBLGNT Greek words. This is neither
unique contextual lexical sense resolution nor a claim that the
source UBS lexicon contains every MACULA source word. The detailed
original-word evidence is stored as a **private, expiring CI review
artifact**, not a published or application-integrated resource.
