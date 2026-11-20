# UBS Hebrew 0.9.4 — bounded contextual pilot on 72 original WLC words

**Result (2026-11-20): NO-GO for automatic promotion of the 53,981
verse-citation-based semantic candidates.** This is an evidence-gathering
pilot, not a revised lexical dictionary or v1.1 publication.

## Actual sample and review method

From the [one-pass source-pinned v1.1 audit](V11_SEMANTIC_FEASIBILITY.md),
select **72 exact original WLC word IDs in 36 authentic UBS 0.9.4
headword families**, deterministically distributed as:

| Source-family frequency stratum | Selected headwords | WLC words |
| --- | ---: | ---: |
| Most frequent | 12 | 36 |
| Middle of ranked families | 12 | 24 |
| Rare (1–3 citation candidates) | 12 | 12 |
| **Total** | **36** | **72** |

For every selected original token, the source-pinned [private witness
generator](build_v11_context_pilot.py) captures the unmodified WLC word
ID, biblical reference, Hebrew lemma, source English, grammatical POS and
morphology, original Strong and SDBH, up to seven neighboring WLC tokens
on each side, the exact UBS candidate LEXID, the other authentic UBS
LEXIDs of that headword, and **original UBS EN/FR sense definitions and
glosses**. The historical v1.0.0 source revisions are unchanged.

The 72-item *original source excerpt screen* is recorded separately in
[v11_contextual_pilot_screening.json](
v11_contextual_pilot_screening.json) and checked against the *original
word-specific source witness* by
[verify_v11_context_pilot_screening.py](
verify_v11_context_pilot_screening.py). The source snippets are only
uploaded as a temporary **PRIVATE 14-day GitHub Actions artifact**.
They are not republished in the repository.

This sample is **stratified, not a uniformly random representative
sample**: it deliberately overweights frequent and low-frequency lexical
families to challenge the general method. Its results **must not** be
reported as the error rate of the 53,981 remaining candidates.

## Actual outcome of the bounded contextual screen

| Independent editorial screening status | Sampled original words | Meaning |
| --- | ---: | --- |
| No obvious semantic contradiction in the *short* UBS/WLC witnesses | **66** | Source-compatible under limited inspection, **NOT** 66 individually certified contextual interpretations |
| Phrase boundary or idiom remains uncertain | **3** | Abstain until complete original syntax is reviewed |
| Apparent candidate sense or source-token granularity conflict | **3** | Do **not** assign the unique verse-witness LEXID |
| **Total** | **72** | **0** new UBS semantic LEXIDs approved |

The six source-specific cautions, with original exact word IDs and the
unmodified UBS lexical alternative inventories, are:

| Original WLC word | Source location | Why source citation alone is insufficient |
| --- | --- | --- |
| `o170050140262` | Esther 5:14 | Original WLC describes advice/proposal pleasing Haman, whereas the cited UBS sense is a thing/event/matter; another UBS speaking/message sense exists. The broad *matter* reading could be defensible, but exclusive contextual precision was not demonstrated |
| `o210110070032` | Ecclesiastes 11:7 | Light is pleasing to the eyes; selected UBS sense describes morally right or beneficial events, whereas another UBS sense describes enjoyable or attractive objects |
| `o090240030172` | 1 Samuel 24:3 | Source WLC token denotes wild goats inside the place phrase *Rocks of Wild Goats*, but the UBS selected sense names the entire place; an alternative UBS sense denotes the animal. Whole-phrase naming is not the same as individual-token semantics |
| `o090050050021` | 1 Samuel 5:5 | Original WLC phrase expresses causation, while UBS's candidate describes manner; the larger expression must be checked |
| `o030140360181` | Leviticus 14:36 | A temporal *after this* construction may not be equivalent to the selected manner sense *thus* for the individual word |
| `o010310240162` | Genesis 31:24 | The fixed idiom *good or bad* in a speech prohibition does not automatically establish the UBS beneficial-event sense |

These are editorial **screening cautions**, not source emendations or
independently proven counter-readings. In particular, the *thing/matter*
sense in Esther 5:14 and the place name in 1 Samuel 24:3 remain genuine
source possibilities under particular interpretations. The pilot tests
whether the **automatic assignment is justified**, not whether any one
dictionary editor must be wrong.

Other sample contexts demonstrated plausible matches, including the
different individuals named Hanun (1 Chr 19:3 versus Neh 3:13), Joah
(1 Chr 26:4 versus 2 Kgs 18:18), Lamech in Seth's genealogy (Gen 5:25),
the place *Valley of Vision* (Isa 22:5), the person Jael (Judg 4:17)
and a lexical animal/placename distinction (1 Sam 24:3). These support
the usefulness of **careful source identity and contextual checking**,
but do not certify a general semantic selection algorithm.

## Recommendation

**NO-GO for bulk adding 53,981 LEXIDs** merely because a dictionary
sense cites the word's verse. This pilot found nontrivial sense and
source-segmentation concerns even after strong lexical identity and
unique-in-verse safeguards. Automated word-level promotion would
misrepresent source-limited confidence.

The narrower positive result is that many original citations are
promising **editorial review candidates**. A separate opt-in v1.1
enrichment may be pursued only if it can show a scalable, generically
justified *word-level* semantic rule that checks contextual morphology,
multiword expressions, competing real UBS sense glosses and exact
original token identity, and independent true/false examples. No
per-verse or named-word code exceptions should be written merely to
force a target coverage percentage.

If no such high-precision generic rule emerges without a major manual
review campaign, accept the published Hebrew **v1.0.0** semantic gap.
The existing 99.022% headword-inventory-scoped **lexical** linking figure
is not a semantic precision estimate. The published v1.0.0 ZIP,
historical original index, MACULA original Strong/SDBH and the Bible
application are all **unchanged**.

## Technical verification boundary

The [GitHub Actions UBS Hebrew workflow](
../../../../.github/workflows/bsi-ubs-hebrew.yml) rebuilds the
complete original WLC v1 lexical candidate, regenerates the 53,981
original-verse witness audit, creates exactly 72 original word context
samples, and verifies the six original-word/sense-specific cautions,
with exact identity and original revision checks. Both sample and
screening checks preserve **0 approved contextual semantics**.

**Technical CI green is not editorial acceptance or publication**. The
human screen above is explicitly limited to the available UBS sense
description and WLC source excerpt; a subsequent professional
whole-verse contextual recheck would be needed to promote specific
senses in an official dictionary mapping.
