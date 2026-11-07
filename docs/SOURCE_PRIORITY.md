# SWORD upstream priority and duplicate-edition policy

Bible Resources publishes **one curated resource per verified edition**. If the
same Bible, commentary or dictionary edition is available from several of our
five supported SWORD repositories, use only the highest-priority eligible
source; do not import or publish a copy from every upstream.

This is an **operational source preference**, not a claim that CrossWire
contains a more recent, more accurate or better-licensed edition.

## Priority (highest first)

1. **CrossWire** (\`crosswire\`)
2. **eBible** (\`ebible\`)
3. **STEP Bible** (\`step\`)
4. **AndBible** (\`andbible\`)
5. **AndBible Extra / Xiphos HTTPS mirror** (\`andbible-extra\`)

The authoritative, reviewable order is in
[\`config/source-priority.json\`](../config/source-priority.json).
Adding or removing a SWORD provider must explicitly update this list.
The order applies equally to Bibles and commentaries; it does not override
copyright, quality review, actual edition identity or publisher provenance.

**Example:** An edition is verified as identical in CrossWire and eBible.
Select CrossWire; mark eBible \`skipped_lower_priority\`. If CrossWire's
catalogue is successfully read and *does not* list that edition, select the
highest available lower source. If CrossWire is **unavailable**, stop: do not
mistake an outage for confirmed absence.

A lower source may offer newer metadata or cleaner text. The rule still uses
the recorded priority. Flag meaningful version, rights and quality differences
for explicit reassessment of the ordering or identity before importing.

## Edition identity is not the SWORD module ID

- \`KJV\` in two catalogues can be two revisions or two different data files.
- Different SWORD IDs can describe the very same edition.
- The title \`Matthew Henry Commentary\` can refer to full, concise,
  abridged, translated or revised texts.
- An edition of a work in another language, with a distinct text, revision,
  abridgment, verse mapping or license is **not automatically** a duplicate.

SWORD \`.conf\` properties such as \`Description\`, \`Lang\`,
\`Versification\`, \`ModDrv\`, \`Version\` and \`TextSource\` are useful
**candidate signals**, not evidence of identical content. Consult the actual
texts and publication history, as well as byte/content hashes where
available, before declaring two sources identical. The separate edition
identity record is
[\`config/edition-identities.json\`](../config/edition-identities.json).

A verified registry entry looks like this **example only** (not an assertion
that these two modules have been compared):

    {
      "edition_id": "example-work-specific-edition",
      "category": "commentary",
      "language": "en",
      "verified_by": "human-reviewer",
      "evidence_url": "https://example.org/documentation",
      "sources": [
        {"provider": "crosswire", "module_id": "ExampleCom"},
        {"provider": "ebible", "module_id": "OtherCom"}
      ]
    }

The actual registry starts **empty**. Every mapping needs deliberate human
verification and evidence; merely sharing an identifier or a title is not
enough. Two *verified different editions* may legitimately share a display
title.

## Selection behavior

\`scripts/select_sources.py\` reads only the five upstream **metadata
catalogues** and the reviewed registry. It never downloads module text and
never writes upstream data.

- Same verified edition in multiple repositories: **select the single
  highest-priority instance**, report the lower entries as skipped.
- Same module ID across providers, without verified mapping: **block for
  identity review**, including cases with conflicting language or category.
- Same title, category and language across providers, but different IDs and
  no verified distinction: **block as a possible duplicate**, never claim
  identity from that title.
- Registered identity with unexpected category/language: **block**.
- Higher-priority catalogue unavailable: **block lower-priority selection**;
  successful absence is different from network failure.
- No candidate collision and all higher-priority catalogues checked:
  **single catalogue candidate** may be selected for *further review*.
  This is not a declaration of content identity or permission to redistribute.
- Completely missing catalogues cause the report to be **incomplete**, even
  if no resource rows exist.
- Multiple different editions deliberately verified as distinct are kept
  separately. If they share a SWORD module ID, further packaging/installation
  conflict review is still required.

Module **source version numbers are not ranked across providers**. The
priority order is explicit. The SWORD content, license, actual source edition
and editorial status are verified only during a later import/release review.
No installed Bible user data, local modules or source archives are changed.

## Run it

    python scripts/select_sources.py --output reports/source-selection.json

The default command exits nonzero if any duplicate candidate is unresolved or
a provider's catalogue is unavailable. For the **read-only scheduled audit**
that must still report all unresolved cases without granting import permission:

    python scripts/select_sources.py --report-only \
      --output reports/source-selection.json

The output contains \`selected\`, \`skipped_lower_priority\`, and \`blocked\`
collections, along with reasons and provider status. Selected here means
**priority candidate**, not approved imported text; all rights and source
normalization gates still apply.

The GitHub Actions source monitor uploads a report and summarized counts,
but there is **no automated importer wired to this selection yet**. The
reviewed importer must consume this result, refuse incomplete/blocked cases,
and only stage and publish one vetted edition. Until then, no automatic
exclusion or deletion of modules in the Bible application's existing library
has been implemented.

## To resolve a flagged duplicate

1. Record the two providers, module IDs, versions, author/work, translation,
   edition/year, language, editorial extent (full/concise/abridged),
   versification and license.
2. Compare the **actual** editions or reliable publisher source evidence; do
   not trust a matching title or ID alone. If they differ, register/review them
   separately and document why.
3. If the exact same edition, register one canonical identity with both
   aliases, reviewer and evidence URL. Run unit tests and repeat selection.
4. Use the highest-priority source that has been confirmed present; retain
   other provider links for monitoring, but do **not** import duplicates.
5. Before release check permissions, structural normalization, source
   fidelity and the compiled SWORD reader test.

Source selection belongs to Bible Resources. The Bible application's existing
downloader is **not** changed by this policy; client migration must be an
explicit, separately reviewed integration task.

## Curated publication identity gate

Every `approved` manifest must carry a stable `canonical_edition_id`
independent of the provider and SWORD ID. The publisher refuses two approved
modules with the same canonical ID **and edition variant** (`faithful` or
`reader_optimized`), even if their module IDs differ. Explicitly reviewed
faithful and reader-optimized variants may coexist; those are editorial
variants, not duplicate provider imports. Canonical IDs must be created from
verified work, language and edition identity, never guessed from titles.

The publication schema/validator prevents **declared** duplicate IDs. It
cannot prove that a curator has not mistakenly assigned two different IDs
to the same edition. The import-review workflow therefore must reconcile
each new edition with the full existing identity catalogue before approval.
