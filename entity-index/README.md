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
**18 exact Hebrew word IDs / 19 source record assignments** absent in the
pinned WLC audit ([inherited ACAI #80](https://github.com/icfmp/ACAI/issues/80)).
All 18 are indirect `subject_referents` source claims, not direct-name words.

This manifest is **data evidence**, not hardcoded logic for specific
biblical entities. During compilation the generic builder checks that every
reported ID is actually present in the input annotations, is linked only by
the audited indirect field, matches the pinned source-edition identifier and
has source provenance. It then retains the original IDs and token groups
**unchanged** inside the derived entity records but removes these 18
unattested IDs from `by_word`. The `unattested_source_words` section lists
each quarantined ID, all affected entity/link-type claims and its exact
audit provenance. Offline resolution returns `unattested_source_word_id`
instead of a false match or a fabricated replacement ID.

**Important:** this is protection against the 18 *already documented*
source-absent IDs, **not** a new full independent comparison of every
original-language word against both pinned texts. The general source
parity audit and source-version/versification compatibility remain pending
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
