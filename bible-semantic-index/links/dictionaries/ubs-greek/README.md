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
python3 -I bible-semantic-index/links/dictionaries/ubs-greek/build_index.py \
  --english ubs-source/dictionaries/greek/JSON/UBSGreekNTDic-v1.0-en.JSON \
  --french ubs-source/dictionaries/greek/JSON/UBSGreekNTDic-v1.0-fr.JSON \
  --macula macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv \
  --output /tmp/ubs-greek-rebuilt.json
python3 -I bible-semantic-index/links/dictionaries/ubs-greek/test_index.py
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

## Source-verified original Greek ambiguous Strong headwords (220 of 224)

The [original 224-token ambiguity classification](audit_224_ambiguities.py)
makes no claim that the historical Strong index should be rewritten.
The exact pinned Greek MACULA source and UBS 1.0 EN/FR headword evidence
independently confirms **one NFC-identical original Greek headword
with a matching original UBS Louw–Nida code for 220 original word IDs**.
Five original lexical families have explicit
[source-word decisions](v1_reviewed_ambiguous_headwords.json):

| Source original lemma | Original Strong | Reviewed word IDs | Reviewed UBS lexical MainId |
| --- | --- | ---: | --- |
| `πόλις` | `4172` | 162 | `004075000000000` |
| `ἐλεάω` | `1653` | 32 | `001661000000000` |
| `πάρειμι` | `3918` | 24 | `003819000000000` |
| `κοπρία` | `2874` | 1 | `002888000000000` |
| `κόπριον` | `2874` | 1 | `002889000000000` |

The [individual-word verifier](build_reviewed_224_ambiguities.py)
requires exact original word ID, unchanged lemma, original Strong,
morphology, verse reference and LN witness, unique matching UBS Greek
lexical entry, authentic UBS dictionary POS, and exact source UBS EN/FR
lexical domain corroboration. It adds a **separate private
`by_macula_ambiguous_word` headword evidence overlay** while preserving
every original MainId in the historical Strong index. Neither this
lexical headword review nor the original LN-domain code determines
a unique contextual semantic `LEXID`.

**Four original ambiguities remain unapproved:** the
original capitalized `Πόλις` (Acts 16:11, no canonically identical
source headword), the separate original `μαράνα` and `θά`
(1 Corinthians 16:22, source Strong `3134`, no individual matching
headword), and one original `πάρειμι` (Luke 11:42) whose
headword matches but lacks source UBS LN corroboration.
These are not converted by guessing case, splitting/recombining
words, or assigning one lexicographic meaning artificially.

**220/224 old source Strong ambiguities now have independently reviewed
original-word headword identities**, but the legacy 224 Strong-derived
multiple-entry candidates are intentionally all retained. This
changes neither the **137,242 / 137,741** Greek word headword coverage
nor source semantics; it adds verified original-word specificity.
The versioned source-reviewed candidate is a **private expiring
Actions artifact**, not a published SWORD module or Bible app integration.

## Source-verified Greek grammatical taxonomy reconciliation — 32 original words

The [explicit taxonomy ledger](v1_reviewed_taxonomy_headwords.json)
records **32 exact original SBLGNT word IDs** whose pinned MACULA lexical
class differs from UBS Greek Dictionary 1.0's *lexicographic* part-of-speech
classification, while the original Greek NFC lemma, unique UBS bilingual
headword identity and original exact UBS Louw–Nida domain evidence agree:

| Original Greek lemma | Original MACULA class | Original UBS class | Original words |
| --- | --- | --- | ---: |
| `τεσσεράκοντα` | numeral `num` | adjective `adjc.` | 22 |
| `ἐνενήκοντα` | numeral `num` | adjective `adjc.` | 4 |
| `ὅστις` | pronoun `pron` | relative pronoun `prel.` | 5 |
| `ὁ` | determiner `det` | article `artc.` | 1 |

These are **different source editorial grammatical taxonomies, not
false lexeme matches**. The
[original-word-specific validator](build_reviewed_taxonomy_headwords.py)
independently checks each word ID, original Strong/morphology, original
Greek/reference and both original EN/FR UBS lexical-domain witnesses,
then modifies **only the private lexical HEADWORD review status**.
MACULA and UBS source POS labels and every original Strong/LN token
remain unchanged. No contextual `LEXID` is selected.

Three authentic original-word cases remain unapproved in the same
original strict-lemma+LN cohort: `ὁπότε` (MACULA conjunction versus
UBS adverb; requires independent syntactic/editorial review), and
`ἄμωμον` and `Ἀρνί` (original Strong `0`; no inferred Strong
equivalence). The 220 previously approved individual-word original
Strong ambiguity headwords remain intact.

The source-reviewed private overlay now has **9,184** individual-word
headwords beyond the historical, unchanged **128,090** Strong-derived
entry candidates: **137,274 / 137,741** (about 99.66%) original Greek
words have independently source-supported lexical headword identities.
This does **not** certify contextual lexical sense accuracy and does
not fill missing UBS entries. The candidate remains **private and
unpublished**; all original sources and the old `index.json` are
preserved.

## Greek headword identities with an original missing Strong annotation

The [explicit two-word review ledger](v1_reviewed_missing_strong_word_headwords.json)
and [independent source verifier](build_reviewed_missing_strong_word_headwords.py)
address two **original SBLGNT word IDs** with MACULA `strong=0`:
`ἄμωμον` (original noun; original UBS lexical noun) and
`Ἀρνί` (original proper noun; UBS proper-name lexical entry).

Both preserve their exact original Greek NFC headword and an original
source Louw–Nida lexical-domain code corroborated independently by the
pinned UBS 1.0 **English and French** dictionary headwords. The original
UBS POS labels are `noun` or `noun-name` in English, and `nom`
in French; these genuine bilingual source labels are intentionally
**not rewritten or translated in the source data**. The absence of
MACULA Strong is a missing *Strong annotation*, not a reason to invent
an original Strong or to map `0` to a universal lexicon key.

These exact two word IDs are source-reviewed for **lexical headword
identity only**, without any inferred contextual UBS semantic `LEXID`.
Their original Strong remains the literal `0`; original spelling,
morphology, LN annotations and references are preserved. The original
`ὁπότε` (MACULA conjunction versus UBS adverb) remains unapproved,
rather than forcing grammatical agreement.

The private source-reviewed Greek word-ID headword count becomes
**9,186**, on top of the historical unchanged **128,090** candidate
Strong-derived words: **137,276 / 137,741** Greek words have a
source-evidenced lexical entry candidate. The remaining **465** source
words comprise this one strict grammar discrepancy, 459 original lemmas
without an NFC-identical original UBS entry, and five original
composite Strong annotations. This is not contextual sense accuracy
or publication readiness. All original dictionary resources,
the SBLGNT TSV, historical `index.json`, and existing ambiguity
candidate lists remain unchanged. Private, expiring CI artifacts
are not publicly released data.

## Independent original Greek missing-UBS-headword census

The [source-pinned 459-word audit](audit_missing_exact_headwords.py)
examines each original SBLGNT word ID for which *no Unicode-NFC-identical
Greek lexical headword* occurs in the original UBS Greek Dictionary
v1.0 EN/FR, preserving every Greek source spelling, Strong, LN,
morphology, word ID and reference. **459 words in 47 original source
families** have this source-specific disposition. Diagnostic
case-insensitive headword comparison, exact UBS original Strong code
presence and merely sharing an Louw–Nida domain code are **not**
automatically accepted as the same Greek lexeme.

The audit finds **456 words without even an original UBS Greek
case-only headword spelling or exact source Strong-code identity**.
The largest such source families are `ἰδού` 200,
`Ἰερουσαλήμ` 76, `ἱερόν` 30, `ἴδε` 30,
`ἕνεκεν` 20 and `περισσότερος` 15. This does
not prove that there can be no related lexical entry under
a different original UBS lemma. An independent source/editorial
equivalence would be required; a matching semantic domain is not enough
to invent an alias.

A small exception consists of **three original MACULA word IDs** for
`Ἄλφα` (original Strong `1`, noun, LN `61.7`).
The original UBS English and French lexica have one lower-case original
headword `ἄλφα`, UBS `MainId=000253000000000`. The
[explicit three-word editorial ledger](v1_reviewed_case_only_alpha.json)
and [original-word verifier](build_reviewed_alpha_case_only.py) require
independent English/French UBS lexical-domain evidence and source
grammatical class **in addition to** a unique case-only Greek headword.
The original uppercase source Greek, original Strong `1`, morphology,
LN and verse reference remain **unchanged**; only those three word-ID
lexical HEADWORD identities are reviewed. This is not an invented
global Strong alias or contextual UBS `LEXID` choice.

The resulting private source-reviewed extra original-word headwords
total **9,189**, plus **128,090** unchanged Strong-based word
candidates: **137,279 / 137,741** Greek word occurrences have
a source-supported lexical headword candidate (approximately 99.66%).
The remaining **462** unmatched original words are the **456** above,
five untouched composite Strong expressions and one authentic
`ὁπότε` source grammatical discrepancy still lacking an approved
source-headword decision. The 220 word-specific resolutions of original
Strong ambiguities are separately retained; all 224 historical
multiheadword Strong candidate lists remain unchanged.

This is **lexical entry/headword evidence only, not accuracy of
contextual semantic senses**. All new evidence is maintained in
private expiring GitHub Actions artifacts, not SWORD or application
downloads. No source Greek or historical `index.json` is modified.

## Source-reviewed composite Strong lexical headwords and coverage accounting

The [composite Strong audit](audit_composite_strong_original_words.py)
identifies **five exact original MACULA word IDs** in three families,
each with one independently source-attested Greek UBS v1.0 EN/FR
lexical headword. The
[explicit source-word review ledger](v1_reviewed_composite_strong_headwords.json)
and [validator](build_reviewed_composite_strong_headwords.py) accept only
**headword identity at those original word IDs**:

| Original Greek lemma | Source Strong (unaltered) | Word IDs | UBS headword MainId | Original UBS Strong (separate) |
| --- | --- | ---: | --- | --- |
| `ὑπερεκπερισσοῦ` | `5228+1537+4053` | 3 | `005125000000000` | `G4053a` |
| `δισμυριάς` | `1417+3461` | 1 | `001382000000000` | `G1364a` |
| `ἐκπερισσῶς` | `1537+4053` | 1 | `001612000000000` | `G4053b` |

Four original word IDs have their own authentic Louw–Nida
corroboration: `78.34`, `60.9` or `78.31` as applicable.
**One original occurrence, `n52005013004` at 1 Thessalonians
5:13, has an empty original LN annotation.** This is explicitly
recorded as **entry/headword only** using its real exact original
Greek lemma and original adverb class; its LN remains empty. The
source LN value must **not** be copied from the other occurrences in
the family. Neither source Strong nor UBS Strong is rewritten or
treated as a universal alias, and no contextual UBS `LEXID` is
inferred.

### Corrected original-word coverage accounting

A source word already present in the review overlay is **not a newly
covered word** merely because its status is promoted from a preview
to an editorially reviewed lexical headword. This is checked
generically by
[the word-coverage invariant validator](validate_word_coverage_invariants.py)
and its negative tests across the complete reviewed candidate pipeline.

| Distinct original-word metric | Count |
| --- | ---: |
| Original SBLGNT word IDs | 137,741 |
| Existing historical Strong-based candidate word IDs | 128,090 |
| Additional **distinct** word-ID lexical entry candidates | 9,195 |
| Original words with **any** lexical entry candidate | **137,285** |
| Of the additional candidates: reviewed headword identities | **9,194** |
| Of the additional candidates: unapproved original preview | **1** (`ὁπότε`) |
| Original words with source-reviewed lexical headwords, including baseline | **137,284** |
| Original words without source-reviewed lexical headwords | **457** |
| Original words without **any** lexical entry candidate | **456** |
| Historical multiple-entry Strong cases (already in baseline, not added again) | 224 |
| Original Strong ambiguity cases independently reviewed by word ID | 220 |
| Original Strong ambiguity cases still unresolved | 4 |

The **456** without any lexical entry candidate have no
NFC-identical or case-only original UBS headword in the pinned UBS
dictionary; they remain unchanged. The single strict preview
`ὁπότε` has a lexicographic taxonomy discrepancy
(MACULA `conj` versus UBS `advb.`) and is not silently approved.
The historic baseline's 224 multiply headed Strong entries are
retained even though 220 have independent original-word lexical
headword evidence.

This final arithmetic distinguishes *candidate coverage* from
*editorially reviewed headword support*, and **neither is a measure
of uniquely determined contextual UBS senses**. No original Greek,
Strong, LN, morphology, verse, historical `index.json` or original
lexicon entry is modified. All reviewed word-level results remain
**private expiring CI artifacts, not a published SWORD resource or
Bible application integration**.

## Original Greek temporal conjunction/adverb lexical headword review

The [independent original source audit](audit_hopote_original_word.py)
identifies the single original MACULA Greek word ID
`n42006003014` in **Luke 6:3**, original Greek
`ὁπότε`, original Strong `3698`, original Louw–Nida
`67.30`, source lexical class `conj` and actual
source morphology **`ADV`**.

The pinned UBS Greek Dictionary 1.0 EN/FR independently records the
NFC-identical Greek headword (MainId `003605000000000`),
lexicographic part of speech `advb.` in both editions, and the
same original Louw–Nida lexical code `67.30`. This reflects
a **lexical versus syntactic grammatical classification**, not a
missing or corrupted original Greek word: temporal adverbials can
introduce clauses. See, as distinct classical grammar background,
[Dickinson College Commentaries, Goodell's Greek grammar,
temporal clauses](https://dcc.dickinson.edu/grammar/goodell/clauses-%E1%BD%85%CF%84%CE%B5-%E1%BD%81%CF%80%CF%8C%CF%84%CE%B5-%E1%BC%90%CF%80%CE%B5%CE%AF-%E1%BC%A1%CE%BD%CE%AF%CE%BA%CE%B1-%E1%BD%81%CF%80%CE%B7%CE%BD%CE%AF%CE%BA%CE%B1)
and [Logeion's Greek lexicon entry](https://logeion.org/%E1%BD%81%CF%80%CF%8C%CF%84%CE%B5).

The [explicit original-word editorial decision](v1_reviewed_hopote_temporal_headword.json)
and [fail-closed verifier](build_reviewed_hopote_headword.py)
source-review only this **original-word lexical HEADWORD identity**.
MACULA original class `conj`, source morphology `ADV`,
Strong, Greek spelling, LN and verse remain **exactly unchanged**.
UBS original `advb.` also remains unchanged. The code does
not infer a contextual UBS `LEXID` or globally equate
`conj` and `advb.` for other words.

With this individual-word review, **all 9,195 additional distinct
Greek original-word lexical entry candidate records have been
editorially reviewed as headword identities**. The unchanged historical
Strong-based 128,090 word candidates bring source-supported lexical
entry *candidate* word coverage to **137,285 / 137,741**
(approximately 99.67%). **456** original SBLGNT words have no
NFC-identical or case-only original UBS Dictionary 1.0 Greek
headword and remain **unlinked**, rather than supplying
speculative synonyms or inflectional Strong aliases. The legacy
224 multiply headed Strong cases are retained; 220 have separate
original-word-specific source review and four remain undecided.

These are **source-attested lexical headword identities, not a
measurement of correct contextual semantic senses**. No contextual
UBS `LEXID` has been inferred, no original source or historical
index modified, and no public SWORD or Bible app release has been made.
Reviewed candidates remain **expiring, private CI artifacts**.

## Authentic UBS AlternateLemmas: 409 original Greek word-ID lexical headwords

A second inspection of the **pinned original UBS Greek Dictionary 1.0
EN and FR data** established that many of the remaining MACULA source
lemmas were **not missing from UBS**: they were listed under the
original dictionary's own `AlternateLemmas` field, rather than under
a separate `Lemma`. This is qualitatively different from inventing
a Greek spelling-normalization or Strong alias.

The [exact bilingual source audit](audit_ubs_explicit_alternate_lemmas.py),
[20-family explicit editorial ledger](v1_reviewed_explicit_ubs_alternates.json)
and [individual original-word verifier](build_reviewed_explicit_ubs_alternates.py)
review **409 exact original Greek word IDs**. Every reviewed word has
one **NFC-identical authentic original `AlternateLemmas`** entry
in **both** pinned UBS languages and an **individual original MACULA
LN code corroborated by both UBS editions**. The original Strong,
Greek spelling, morphology, syntactic class, reference and word ID
remain unchanged. No contextual `LEXID` or universal Strong alias
is inferred, even when UBS source Strong differs from MACULA.

Important high-volume examples, each attested directly in UBS source:

| MACULA source Greek | Source words | Exact original UBS main lemma | Original UBS MainId |
| --- | ---: | --- | --- |
| `ἰδού` | 200 | `ὁράω` | `003615000000000` |
| `Ἰερουσαλήμ` | 76 | `Ἱεροσόλυμα` | `002418000000000` |
| `ἱερόν` | 30 | `ἱερός` | `002417000000000` |
| `ἴδε` | 30 | `ὁράω` | `003615000000000` |
| `ἕνεκεν` | 20 | `ἕνεκα` | `001766000000000` |
| `περισσότερος` | 15 | `περισσός` | `003959000000000` |
| `Ἰσκαριώτης` | 8 | `Ἰσκαριώθ` | `002468000000000` |
| `πλατεῖα` | 6 | `πλατύς` | `004022000000000` |

The other 12 reviewed original lexical families account for
24 word IDs. For example, `ἰδού` and `ἴδε` have original MACULA
classes `ptcl` or `intj` although UBS associates them as genuine
lexical alternatives under the verb `ὁράω`. This approves
**headword/lexeme identity only**, not a claim that the original
token has verb syntax, nor that an individual UBS contextual
sense is known. Likewise, `ἱερόν` is recorded as a substantive
or adjective by MACULA but under the adjectival lexeme `ἱερός`
by UBS. **Preserve both editorial source analyses**, with no
rewritten morphological annotation.

Of the earlier 456 source words, **47** have no matching authentic
original UBS `AlternateLemmas` with an individual original LN
corroboration and remain **unlinked**. The
[non-authoritative accentless diagnostics](audit_456_lexical_variants.py)
found three different Greek spellings that resemble UBS headwords
and share an LN code, but these **were not automatically linked**;
similarity is not source-equivalent lexical identity.
The source-audit records blank values in some authentic UBS
`AlternateLemmas` lists as source metadata defects and excludes
them without creating invented entries.

**New independently verified private lexical headword coverage:**

| Distinct original-word metric | Count |
| --- | ---: |
| Original MACULA SBLGNT Greek word IDs | 137,741 |
| Historical unchanged Strong-derived candidate words | 128,090 |
| Additional **distinct reviewed original-word headwords** | **9,604** |
| Original words with supported lexical headword candidates | **137,694 (99.966%)** |
| Original words with no approved UBS Greek 1.0 headword | **47** |
| Historical multi-headword Strong words unchanged | 224 |
| Separately original-word source-reviewed ambiguous Strong cases | 220 |
| Remaining historic word-ID ambiguity decisions | 4 |

This is a **headword/entry coverage measure, not contextual-sense
accuracy**. The original `index.json`, Greek, source Strong,
morphology, LN, verse references and both UBS original dictionaries
remain byte-for-byte unchanged. The new candidate overlay is only
a **private, expiring CI artifact**. No SWORD resource, public
redistribution or Bible app integration was performed.

## Final unmatched Greek original words — source editorial report

The separate [47-original-word source editorial report](remaining_47_source_editorial_report.md)
enumerates all **26 source lexical families** (47 exact original word
IDs) left unmatched after direct UBS primary headword, exact
English/French authentic `AlternateLemmas` and original
`BaseForms.Inflections` metadata checks. All individual original
word-ID witnesses, authentic Greek spelling, original Strong, LN,
morphology and references remain recoverable from the pinned-source
[read-only audit](audit_last_47_lexical_forms.py).

No original UBS source inflection matched those original MACULA
lemmas as an exact Greek entry. The original UBS source also has
semantic-domain related entries for many of the 47 words, but
**semantic-domain overlap is not evidence of lexical headword
identity**. The 47 original words remain intentionally **unlinked**.
Any future correction requires independent genuine Greek morphological
or lexicographic evidence and a documented per-word editorial
decision, preferably also proposed upstream to UBS source maintainers.

There are **no further automated or source-explicit matching
opportunities demonstrated by these pinned UBS v1.0 fields**. This is
not a claim that the 47 Greek words lack meaning, nor that another
independent lexicon cannot authoritatively establish a match. The
candidate remains private and unpublished, with the original
index and source text unchanged.

## Contextual UBS Greek LEXID source-candidate phase (private, provisional)

The [independent original-word sense census](audit_contextual_sense_candidates.py)
reopens **all 137,741 original MACULA SBLGNT Greek word IDs** using the
pinned UBS Greek v1.0 English/French `MainId`, `LEXID`, and
`LEXEntryCode` inventories. It preserves every authentic word's
original Greek spelling, Strong, Louw–Nida code(s), morphology,
part-of-speech class, reference and immutable word ID. Every
word's lexeme is drawn from the already reviewed lexical headword
overlay or original untouched Strong crosswalk. Bilingual source
identifiers agree exactly; original UBS senses with **blank LN
codes** remain original source senses but cannot be used as
word-specific LN evidence.

The fully source-pinned corpus audit classifies original words as:

| Original-word semantic **candidate** disposition | Count |
| --- | ---: |
| Exactly **one** source-attested UBS LEXID under the supported headword, with matching original word LN code | **122,504** |
| More than one original UBS LEXID under a supported headword and original word LN code(s) | **2,728** |
| No original MACULA LN code matching a UBS sense under the supported headword | **12,458** |
| No source-supported UBS Greek 1.0 headword | **47** |
| Original Strong still offers multiple unresolved UBS headwords | **4** |
| **Total original SBLGNT Greek word IDs** | **137,741** |

The [private, reversible provisional candidate builder](build_provisional_context_sense_overlay.py)
regenerates two separate ephemeral artifacts. One maps each of the
**122,504** original word IDs to its single authentic UBS Greek
`MainId` and `LEXID`, with individual original word-ID
`LEXEntryCode`/Louw–Nida witnesses and status
`PROVISIONAL_unique_original_source_attested_LN_and_UBS_LEXID_NOT_contextually_verified`.
The other retains **all 15,237** original unresolved word IDs, authentic
source code and available UBS candidates, and grouped priorities for
independent editorial decisions. Neither artifact modifies the
historical `index.json`, the 9,604 reviewed lexical headword overlays,
the MACULA corpus, the UBS original dictionary or the Bible app.

**Crucial distinction:** uniqueness in the original UBS lexeme/LN
intersection establishes a **particularly strong source-supported
candidate**, not independently proven correctness of the
Greek contextual meaning in its verse. These 122,504 private candidates
are *provisional editorial choices*, **not 122,504 independently
validated interpretations**. They may be promoted only under a
documented contextual verification policy and targeted spot-checks.
The 2,728 ambiguous sense candidates are preserved without choosing
a particular `LEXID` merely to increase coverage. The 12,458
original LN mismatches must be triaged into missing original
source annotation, independent source system differences or genuinely
non-corresponding senses, **never resolved by inventing LN codes**.
The remaining 47 source-unsupported headwords and four original
Strong ambiguities retain their previously documented status.

All semantic overlays are **private, reversible, source-pinned
14-day GitHub Actions artifacts**. There is **no public SWORD
publication, no contextual-sense validation claim, and no redistribution
of UBS definition texts**. Later publication still requires the
project owner's separate release authorization and license validation.

## Pragmatic review of contextual sense gaps: lower-confidence editorial defaults

The [full original-source 15,237-word priority audit](audit_unresolved_semantic_priorities.py)
shows how to distinguish genuinely different failure modes:

| Original-word contextual-sense source limitation | Word IDs |
| --- | ---: |
| Original MACULA LN **blank**, more than one authentic UBS LEXID in the approved headword | 9,125 |
| Original MACULA LN **blank**, exactly one authentic UBS LEXID | **120** |
| Original MACULA LN present but **not attested** under the approved UBS headword, more than one UBS LEXID | 688 |
| Original MACULA LN present but **not attested**, exactly one UBS LEXID | **50** |
| Original MACULA LN present but not attested and **no UBS lexical senses with an original LEXID** under the approved headword | 2,475 |
| More than one UBS LEXID consistent with original source word-specific LN | 2,728 |
| Historical original Strong still has more than one UBS headword | 4 |
| No source-supported UBS lexical headword | 47 |
| **All unresolved source words before lower-confidence provisional review** | **15,237** |

The original `εἰμί` family alone accounts for **2,456** words
whose original MACULA LN code cannot find any authentic UBS lexical
sense under its correct lexical headword. This is a **source
inventory difference**, not a reason to manufacture a `LEXID`
or rewrite MACULA's original LN annotations.

Under the owner's pragmatic editorial policy, the
[lower-confidence single-sense stage](build_lower_confidence_single_sense.py)
**separately** offers a reasonable, explicitly provisional editorial
default for the **170 original word IDs** where the independently
supported original UBS headword genuinely has **only one original UBS
LEXID**, although the word has either **no MACULA LN code (120)** or
**a nonmatching original MACULA LN code (50)**. This lower-confidence
layer is never merged with the **122,504 original-LN-corroborated
single-sense candidates**, and neither is described as
independently proven contextual meaning. The remaining **15,067**
original source word IDs still lack a uniquely justified provisional
`LEXID`. All source code differences are explicit and reversible.

**Current private provisional semantics:** 122,504 stronger
original-LN-supported word-ID sense candidates, plus **170** separate
weaker, source-only single-LEXID defaults. **Zero** finished,
independently verified contextual sense decisions and **zero**
publicly published resources in this phase. The next quality gate is
targeted contextual editorial validation, with priority on the
2,728 cases where original LN evidence is genuinely multi-valued
and the high-volume particle/preposition families.


## Public identifier-only UBS Greek crosswalk v0.1.0 (published 2026-11-20)

[Download the published standalone BSI UBS Greek crosswalk](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-greek-v0.1.0). The release contains an identifier-only, offline, CC BY-SA 4.0 JSON ZIP and SHA-256. Source word IDs, authentic UBS MainId/LEXID identifiers, explicit provisional evidence and ambiguity statuses are included; original Greek/Strong/LN/morphology, verses, glosses and dictionary definitions are **not** distributed. This release **does not** constitute independent contextual semantic validation, nor a SWORD module or integration into `icfmp/Bible`.

The full **private** evidence/witness index described below remains unpublished and regenerable. Public release scope, source attribution and third-party rights limitations are in [RELEASE_READINESS.md](RELEASE_READINESS.md).

## UBS Greek v1 — finalization policy and complete private original-word lookup

**Editorial stopping decision (2026-11-20):** Do not force UBS Greek 1.0 to
100% word-level sense coverage. Treat source-limited ambiguity as an
acceptable, documented outcome. The lexical headword index is substantially
complete, while a UBS contextual `LEXID` remains a provisional candidate
unless it has undergone independent verse-context semantic validation.

[The consolidated v1 builder](build_consolidated_v1_review_index.py)
reproduces a complete **137,741-original-word-ID** lookup from pinned,
separately source-verified artifacts. Its five *disjoint* provisional sense
tiers are:

| Original UBS/MACULA evidence tier | Original word IDs | Meaning |
| --- | ---: | --- |
| Unique UBS LEXID supported by original word's LN | 122,504 | Stronger source-backed provisional candidate |
| Sole authentic UBS LEXID but source LN absent/mismatched | 170 | Weaker editorial default; preserve mismatch |
| Distinct source-attested UBS Greek form within shared LN | 223 | Reversible form-based candidate |
| One authentic UBS LEXID citing the word's verse and only one source-attested lexical headword there | 258 | Verse-citation-supported provisional candidate |
| Unique authentic UBS source locator after independently calibrated MACULA ordinal | 40 | Lower-confidence locator-supported candidate |
| **Total provisional unique UBS LEXID suggestions** | **123,195 (89.44%)** | **Not 123,195 independently validated contextual meanings** |

The remaining **14,546** original words are *not* assigned an arbitrarily
chosen contextual LEXID. The consolidated lookup instead offers:

| Result | Original word IDs | Consumer behavior |
| --- | ---: | --- |
| `provisional_ubs_lexid` | 123,195 | Offer UBS entry and source-supported candidate; expose evidence tier and provisional status |
| `ubs_entry_only` | 12,288 | Offer the source-supported UBS headword, no invented sense |
| `ambiguous_ubs_senses` | 2,207 | Offer original source UBS LEXID candidates without a forced default |
| `ambiguous_ubs_headwords` | 4 | Preserve alternative original UBS headword entries |
| `missing_ubs_headword` | 47 | State that the pinned UBS edition lacks an approved match |
| **Original Greek word inventory** | **137,741** | One record per original MACULA word ID |

The original **137,694 / 137,741 (99.966%)** source-supported *lexical
headword coverage* and the historical frozen [index.json](index.json) are
unchanged. A lexical headword link does **not** imply that the dictionary
edition contains an appropriate original sense ID; particularly, UBS 1.0
has no original `LEXMeanings` for `εἰμί` and the correct handling is
entry-only.

The private v1 result uses:

```python
from pathlib import Path
import json
import runpy

root = Path("bible-semantic-index/links/dictionaries/ubs-greek")
lookup = runpy.run_path(str(root / "build_consolidated_v1_review_index.py"))["lookup"]
candidate = json.loads(Path("/tmp/bsi-ubs-greek-v1-consolidated-original-word-index-PRIVATE.json").read_text())
word = lookup(candidate, "n40001001003")
# word["status"], word["ubs_main_ids"], word["provisional_ubs_lexid"],
# word["ubs_lexid_candidates_from_original_ln"], word["evidence_tier"]
```

This is a **private research/provisional review artifact**, not the public
runtime format. The complete original-word index is reproduced by the
source-pinned GitHub Actions workflow with original UBS EN/FR Dictionary 1.0,
MACULA SBLGNT, all previously reviewed word-specific source decisions and
exact lexical evidence cross-checks. CI uploads it as an **expiring private
14-day artifact**, not as a tagged release or public downloadable module.
The original Greek, Strong, Louw–Nida, morphology, verses, and UBS
dictionary definitions are never rewritten or bundled.

**Licensing and release boundary:** UBS Greek Dictionary source is licensed
CC BY-SA 4.0 (United Bible Societies); MACULA Greek Linguistic Datasets
(© Biblica, Inc.; hosted by Clear.Bible) are licensed CC BY 4.0, **but the
pinned MACULA source explicitly identifies third-party material and UBS
MARBLE annotations “used with permission”**. See the original upstream
notices and [exact-source release-readiness audit](RELEASE_READINESS.md)
before treating any particular output field as redistributable. A later
separately approved redistribution must preserve
applicable attribution, license and share-alike obligations. The review
index stores identifiers and original MACULA lexical witness metadata,
**not UBS copyrighted definitions or verse text**. No Bible app integration,
SWORD publication or public release is authorized merely by completing
this audit.

**Completion is not publication.** Once the full pinned-source tests pass,
the v1 *research alignment* may be considered functionally finished with
documented limits. Owners must separately authorize any public resource or
downstream integration after rights and editorial acceptance review.
