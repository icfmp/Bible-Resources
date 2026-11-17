# Bible Entity Index — independent offline resource (bootstrap)

This directory is a **portable, independent dataset builder**. It is currently
hosted under Bible-Resources until a dedicated repository can be created. It
does **not** publish or modify any existing SWORD resource or catalogue.

## Scope

ACAI provides an initial *historical data witness*, not an unquestioned
authority. The output is an **offline lookup index** from an exact,
edition-qualified original-language word ID to zero, one or **multiple**
candidate biblical entities. It is not an automatic theological,
biographical, genealogical or lexical interpretation engine.

The current input is the **self-hosted frozen fork**
[icfmp/ACAI](https://github.com/icfmp/ACAI), locked to commit
`e80a874e8282f996199c595378a3b3b9a43aac22`. Rebuilds read a local
checkout at that exact revision. A later independent repository can keep the
same frozen snapshot internally instead of cloning the fork. Normal application
use **never contacts ACAI, Macula, TIPNR or an API**.

### Retained in the derived index

- Source entity ID, proposed output ID, canonical ID, type and **per-record
  SHA-256** of the exact original JSON (provenance, not a license waiver).
- Original ORG verse references and key references as *source claims*.
- Each exact ordered original-word group from `explicit_instances`,
  `pronominal_referents` and `subject_referents`; **repeated groups remain
  repeated**, as multiplicity semantics are not settled.
- The inverse lookup from `corpus:original-word-id` to **all** entity/link-type
  candidates. No first-result-wins behavior.
- Reviewed, source-cited editorial decisions, including exact group additions
  and removals in the **derived output only**. Quarantined source records
  remain present and byte-for-byte unchanged in the original fork.

### Intentionally excluded from the consumer resource

The source's multi-language `localizations`, descriptions, biographies,
`speeches`, speculative genealogy, coordinates and encyclopedia/dictionary
prose are **not** copied into the derived index. Exclusion is a *format scope
decision*, not a claim that those fields never existed. Speech attribution and
family relations need their own verified provenance and separate schema before
reintroduction. Future language packs will supply labels/articles without
changing entity IDs. Strong numbers are **lexicon cross-references**, never
proof of an exact token identity; this phase does not infer a Strong crosswalk.

The imported records not individually reviewed carry
`review_status=source_unreviewed`. Their word links are **candidate source
annotations**, not certified identifications. A reviewed record is reviewed
only for the stated, source-cited editorial decision, not for every fact
conceivably implied by that entity.

## Initial independent editorial corrections

The declarative file `editorial-decisions.json` describes all changes.
The builder contains **no chapter-specific or entity-specific code path**.

- `person:Jashar` becomes `work:BookOfJashar` — **literary work**, not a
  fictional male person. The two existing Hebrew adjective IDs remain exact
  title-**epithet** anchors, not made-up word IDs for the entire title.
- `person:Perez-uzzah` becomes `place:PerezUzzah`; keep the verified
  compound place name from 2 Samuel 6:8, add the exact second source compound
  from 1 Chronicles 13:11. This is distinct from the man Uzzah.
- The place-only two-word group is removed from the **derived**
  `person:Uzzah` explicit-name index. All genuine name tokens remain.
- `person:Hammelech` is **quarantined** from public identity lookup,
  rather than asserting that the Hebrew common noun “the king” identifies a
  historical man. No new identification of Jeremiah's kings or fathers is
  invented.
- `person:Philistine` is **quarantined** as a fictitious singular man;
  the two attested **plural gentilic** word IDs of Genesis 10:14 and
  1 Chronicles 1:12 become source-verified additions to the existing
  `group:Philistine` record. The 20 original speaker spans are **not**
  indiscriminately copied to the group and remain preserved in frozen ACAI.
- `person:Shiloh` is **quarantined**: Genesis 49:10 attests a
  debated expression, but not a demonstrably historical man living in the
  patriarchal age. Its exact Hebrew word remains in the frozen source for
  text-critical and Christological review.
- `person:Johanan` is now **canonically distinct** from
  `person:Jehoahaz.3`: the exact Hebrew token in 1 Chronicles 3:15
  (`o130030150041`) says *Johanan*, not *Jehoahaz*. It remains in
  Johanan's original source group and is removed **only** from the
  derived Jehoahaz direct-name occurrences. The separate Shallum at
  `o130030150101` is now reviewed separately against the Josiah
  royal family and identified with Jehoahaz as below.
- `person:Dishon` (son of **Seir**) no longer claims either of the
  two explicit names in 1 Chronicles 1:41, where the contextual subject
  is the **other Dishon, son of Anah** (`person:Dishon.2`). The exact
  original WLC words `o130010410031` and `o130010410051` remain under
  `person:Dishon.2`; the false verse reference `13001041` is removed
  *only* from derived `person:Dishon`. This resolves two explicit
  homonym collisions without suppressing either historical man.
  **Caution:** the pinned Hebrew of Genesis 36:26, source word
  `o010360260031`, has lexical form **Dishan** (דִּישָׁן), distinct from
  the other `Dishon` forms. We preserve its source assignment rather
  than guess whether the text intends a name variant or another person.
  Every removal is listed in `editorial-decisions.json`; the builder
  refuses an absent/ambiguous `remove_references` request.
- `person:Shallum.5` (1 Chronicles 3:15, exact WLC word
  `o130030150101`, *Shallum*) now resolves canonically to
  `person:Jehoahaz.3` — Josiah's successor named in Jeremiah 22:11
  and 2 Kings 23:30–31. This traditional and academically supported
  identification is documented by
  [SIL translation notes](https://tips.translation.bible/story/translation-commentary-on-1-chronicles-315/)
  and study commentaries. The source's distinct name record,
  exact token, references and original genealogy remain intact.
  `person:Johanan` remains a **different individual**, not a second
  name for Jehoahaz. This adjudicates the royal name-form confusion
  without claiming that disputed chronological birth order is settled.
- `place:Gadara` is **canonically distinct** from `place:Gerasa`:
  Gadara (Umm Qais) and Gerasa (Jerash) are historically separate Decapolis
  cities (UNESCO's [Gadara documentation](https://whc.unesco.org/en/tentativelists/1558/)).
  The source's `place:Gadara.primary_id=place:Gerasa` was a false
  historical city identity merger. The original Gospel **regional demonym**
  tokens and verse references are *not* silently reassigned: Matthew 8:28
  still produces **ambiguous regional/site candidates**, rather than an
  invented precise location. `place:Gadara.2` (Gadara of Perea) remains
  its own distinct canonical entity. See [inherited ACAI #7](https://github.com/icfmp/ACAI/issues/7)
  for textual variants and unresolved geographical scope.
- `keyterm:Universe` and `keyterm:World` retain their distinct source
  records and word groups, but no longer resolve canonically to
  `keyterm:Ability` simply because the input had an overly broad
  `primary_id`. This is identity separation, not a judgment about
  a particular original word's contextual sense.

The remaining inherited editorial/source-fidelity work is tracked in
[Bible-Resources #299](https://github.com/icfmp/Bible-Resources/issues/299).
The old ACAI issue history remains available as evidence; transfer to one
tracker is **not** equivalent to fixing or validating those records.

The original ACAI IDs survive under `source_id` and the original source
commit. Crosswalk clients **must not** interpret a historical `person:`
identifier as an active person automatically.

## Build and verify

From a machine with Python 3.10+ and an exact local checkout of the frozen
input (no Python dependencies):

```bash
python3 -I entity-index/test_build.py
python3 -I entity-index/compile_index.py \
  --source /path/to/pinned-ACAI \
  --verify-source-commit \
  --output entity-index/dist/index.json
```

`.github/workflows/entity-index.yml` repeats these steps, checks the final
corpus size and reviewed examples, then **uploads a CI-only JSON artifact**.
No existing Bible-Resources release, SWORD module or catalogue is changed.
The builder aborts on incomplete input, duplicate entity IDs, unknown editorial
targets, malformed links or edits that cannot be applied exactly. Source files
are never opened for writing.

## Data contract (v1)

`index.json` has `schema_version=1`, `provenance`, `statistics`,
`quarantined`, `entities`, and `by_word`. Each `by_word` key is
`wlc:o...` or `sblgnt:n...` and maps to an **array**, not a single winner.
`link_type` retains whether the evidence came from an explicit original
word, pronoun or subject pointer. For a selected token, consuming applications
must **also check the source corpus revision, verse context and confidence**:
a source word may be shared by two entities, an indirect association may not
be verified, and different textual editions/versifications cannot be silently
equated. The index does not assert that ACAI's every `references` entry is
attested by the pinned critical text.

## Pinned-source original-word absence protection

The independent index must not present a missing original word ID as if the
reader clicked an existing word. A source-version-bound manifest
[`source-unattested-words.json`](source-unattested-words.json) records the
**18 exact Hebrew word IDs / 19 raw source word assignments** absent in the
pinned WLC audit ([inherited ACAI #80](https://github.com/icfmp/ACAI/issues/80)).
All 18 are indirect `subject_referents` source claims, not direct-name words.

This manifest is **data evidence**, not hardcoded logic for specific
biblical entities. During compilation the generic builder checks that every
reported ID is actually present in the input annotations, is linked only by
the audited indirect field, matches the pinned source-edition identifier and
has source provenance. It then retains the original IDs and token groups
**unchanged** inside the derived entity records but removes these 18
unattested IDs from `by_word`. The `unattested_source_words` section lists
each quarantined ID, the **distinct** affected entity/link-type pairs and its exact
audit provenance. The `unattested_raw_word_assignments` statistic separately
counts *all original source-word assignments including any repeated groups*,
so multiplicity is not mistaken for an additional independent entity. Offline resolution returns `unattested_source_word_id`
instead of a false match or a fabricated replacement ID.

**Important:** this is protection against the 18 *already documented*
source-absent IDs, **not** a new full independent comparison of every
original-language word against both pinned texts. The general source
parity audit and source-version/versification compatibility remain pending
in [#299](https://github.com/icfmp/Bible-Resources/issues/299).

## Greek verse inventory compatibility — not a versification rewrite

The pinned Macula SBLGNT original-word inventory and imported ACAI source
reference claims disagree on **eight verse identifiers (22 entity-reference
claims)**. The exact evidence is separately recorded in
[`source-unattested-verses.json`](source-unattested-verses.json), sourced from
the full original audit [ACAI #88](https://github.com/icfmp/ACAI/issues/88).
The original source verse references **remain unchanged** in each entity
entry. The derived `unattested_source_verses` section marks each affected
verse with the source edition, exact claimant entity IDs and provenance.

An exact Greek word lookup in one of those verses receives the status
`verse_not_in_pinned_original_word_inventory` rather than a fabricated
source word or a misleading plain `no_indexed_entity`. This is **strictly
about missing verse IDs in our pinned word-inventory witness**, not a claim
that the verse is universally absent from the Bible or should be renumbered.
Matthew 23:14 and Acts 8:37 are textual variants, while 2 Corinthians 13:14
reflects a source-versification mismatch relative to 13:13. Romans 16:25/27
also require a distinct pinned-source completeness and traditional epistle
subscription review (see inherited #86). Variant provenance is therefore
retained for later source-specific qualification.

## Repeated original-word group semantics and source QA

The inherited [ACAI #195](https://github.com/icfmp/ACAI/issues/195)
documents repeated indirect word groups, especially in pronoun and subject
annotations. A repeated group can represent multiple semantic source links
(e.g. parallel subject and frame references), not an accidentally doubled
biblical word. **No repeated group may be removed merely to reduce a count.**

Our independent CI reuses the existing **pinned** self-hosted source auditor
`/tmp/acai-frozen/.github/scripts/audit_duplicate_word_groups.py`
directly against the exact locked ACAI checkout. This deliberately avoids
maintaining two diverging implementations. It uploads a separately labeled
QA-only `source-multiplicity.json` with every candidate, totals, source
record and field/corpus. The workflow independently checks internal
counts, absence of repeated direct `explicit_instances` and that **all
repeated indirect groups in active derived entries have exactly the same
multiplicity as in the original**. Quarantined source records remain in
the immutable checkout and are included in the audit census.

The normal `by_word` index presents **unique entity/link-type candidates**
per token for the UI and does not imply those repeated raw source assignments
were editorially declared redundant. Historical figures (105 affected
records, 593 extra copies and 24 overlapping word IDs) are **not blindly
assumed to apply** without checking this particular frozen revision.

No original word groups or Scripture are changed. The remaining question
of whether an import created some redundant repeated indirect edges
requires original Macula pointer-channel provenance, not a shortcut
using `set()` on the source JSON.

## Full exact-word distinct-person collision audit

The independent `audit_person_overlaps.py` reads our **complete generated
index**, not the outdated historical list of 93 source collisions from an
earlier ACAI revision. It detects when two or more *different canonical
people* claim **one identical original-language word ID**, and separates:

- `multiple_explicit_names`: two different people claim the same explicit
  original-language name token — **highest manual-review priority**;
- `mixed_name_and_indirect`: one explicit name intersects another person's
  pronoun/subject pointer — contextual evidence required;
- `indirect_only`: multiple person referent annotations on one token;
  these can be legitimate reference multiplicity, **not automatic errors**.

Aliases resolving to one canonical ID are not counted as competing people.
Non-person entities are ignored in this *person-specific* audit. It never
deduplicates source groups, changes source evidence, merges individuals or
accepts a token based solely on Strong/lemma/name spelling.

CI regenerates `dist/person-overlaps.json` deterministically from all
6,644 frozen ACAI source records and uploads it as **QA-only evidence**,
alongside the unapproved local index artifact. The concise CI log exposes
the highest-priority collisions for source-by-source follow-up under
[inherited identity issue #75 / our tracker #299](https://github.com/icfmp/Bible-Resources/issues/299).
A count from an old unpinned snapshot is not a release gate.

## Original corpus labels and stable client-facing corpus names

The pinned ACAI source spells its Greek occurrence field **`SBLGNT`**
(uppercase), while the public resolver API uses the canonical name
**`sblgnt`** (lowercase). Before this repair, the generic compiler
preserved source spelling in its inverse word-key index, causing valid
Greek `sblgnt:n...` lookups to silently return zero candidates.

The pinned `source.lock.json` now carries the **explicit source-corpus
crosswalk** (`SBLGNT -> sblgnt`, `wlc -> wlc`); input occurrence
group names and token arrays are retained **byte-for-byte in meaning** and
original source JSON is untouched. Only inverse exact-word lookup keys
are normalized. Unknown source-corpus labels and contradictory source word
prefixes cause a build failure; no implicit uppercase/lowercase guessing.

A real-corpus QA proof verifies `sblgnt:n45016001004` in Romans 16:1
resolves to `person:Phoebe` under the pinned Macula Greek edition.
Greek negative-lookup checks alone are **not** enough to demonstrate that
the index really supports Greek original-word lookup.

## Version-specific reference provenance: variants and subscriptions

A verse reference can have editorial or historical interest without a matching
word in the *specific pinned Greek edition* used for lexical navigation.
The independent `source-reference-qualifications.json` manifest records
**12 audited source-record/verse claims**, with the exact source record,
verse, pinned edition, classification and written evidence:

- **2** alternate textual reading/identification cases:
  `place:Bethabara` (John 1:28, where pinned SBLGNT reads *Bethany*)
  and `place:Trogyllium` (Acts 20:15, absent as a name in pinned SBLGNT).
  These are **not deleted** and are not misrepresented as SBLGNT word hits.
  They remain candidates for a separately sourced textual tradition.
- **10** named **traditional subscription candidates** drawn from the
  validated sample in inherited [ACAI #86](https://github.com/icfmp/ACAI/issues/86):
  Phoebe, Cenchreae, Corinthus, Achaicus, Fortunatus, Epaphroditus,
  Philemon, Nero, the Caesar.3 alias, and Pacatiana. The names are not
  attested by the relevant SBLGNT letter-final verse, even though
  traditional subscriptions may contain them. The designation
  *candidate* distinguishes this diagnostic from a full critical edition
  of every letter's subscription history.

Each claim is attached **only** to the original record and verse for which
the source reference already exists. The builder rejects missing source
records, unreferenced verses, duplicate classifications, wrong source
editions, missing proof and claims with a **real original-language word
anchor in that verse**. The resulting `qualified_source_references`
is a corpus+verse keyed evidence index. It **does not** alter the original
`references`, `key_references`, word groups, Bible text or versification.
It also does not imply the entire 6,641-entry dataset has been reviewed.

Further full-epistle subscription and variant-source checks remain tracked
in [#299](https://github.com/icfmp/Bible-Resources/issues/299).

## Offline lookup and uncertainty handling

`resolve.py` exposes `EntityResolver`. It requires a corpus name, its
**exact pinned edition identifier**, an original word ID and its original
eight-digit ORG verse ID. Its outcomes distinguish an unavailable corpus,
an incompatible edition, malformed identifiers, verse mismatch, no indexed
entity annotation, a source identity candidate and multiple conflicting
canonical identity candidates. **No candidate is called verified solely
because ACAI assigned it a token.** The resolver also reports when the
entity's separate source reference list omits the token's verse.

The `provenance.source_editions` metadata is data-driven, so different
language packs can use one shared identity contract without depending on
language-specific labels. Example after generating the index:

```bash
python3 -I entity-index/resolve.py \\
  --index entity-index/dist/index.json \\
  --corpus wlc \\
  --edition 'Clear-Bible/macula-hebrew@47db250bd55d0d8577f2a94fba114ef16c35b23c' \\
  --word-id o060100130142 --verse-id 06010013
```

This is a **data lookup**, not a final historical interpretation. An
unrecognized source word is not automatically an ordinary lexical word:
the annotation may be missing. No network, Strong-based guessing, or
unverified translation-to-source alignment is used.

The offline producer is independent of the GTK Bible application. This
prepares a source for a future **single** contextual entity resolver, aligned
with [Bible issue #284](https://github.com/icfmp/Bible/issues/284), without
duplicating that app's engine or changing its current user interface.

## Rights and release boundary

ACAI data are **CC BY-SA 4.0**. The derived index must preserve attribution,
the license link and a changes notice, and be shared under **CC BY-SA 4.0**
if publicly distributed:
[ACAI license](https://github.com/icfmp/ACAI/blob/main/LICENSE.md).
Original author credits: BiblioNexus, Mission Mutual and their credited data
contributors. Our changes are independently reviewed and are not endorsed by
those original organizations.

No original Bible text, Macula XML/TSV, third-party dictionary article or
SWORD translation is bundled in this output. The first generated artifact is
**a technical QA build, not an approved public resource**. Prior to any
distribution or consumer integration, we must review the complete original
word/corpus compatibility, remaining identity collisions and publication
provenance, then explicitly approve a release. Independence means owning the
pipeline and decisions, **not inventing evidence**.

## Next stages

1. Validate every source token and reference against the pinned original
   sources while retaining variant-versification provenance.
2. Migrate confirmed identity defects through versioned declarative
   decisions, with explicit retired-ID crosswalks.
3. Define compact resource packaging, checksums and a rights-reviewed
   downloadable release, then wire Bible's shared offline resolver to it.
