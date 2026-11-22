# Source identity and duplicate-edition policy

Bible Resources curates **a verified edition**, not an upstream SWORD package ID.
Every new or updated resource must start from a documented, authorized original
source (preferably a publisher-maintained OSIS or another justified standard),
with an immutable hash, exact edition identity, rights evidence and reviewed
transformation history. Upstream SWORD catalogues are discovery and update
monitoring inputs only, not a ranked automatic import queue.

## Identity, not provider order

- Never infer same-edition identity solely from a title, module ID, language,
  release number, translation family or a SWORD `.conf` record.
- Compare authoritative original sources, edition/revision, language,
  completeness (full/concise/abridged), textual basis, annotations,
  versification and rights. Preserve the evidence for every alias decision.
- Two providers offering the **verified same edition** do not justify two
  independent published resources. Keep aliases for provenance and monitoring.
- Distinct reviewed editions, translations or editorial variants must not be
  silently conflated. An unresolved possible duplicate **blocks approval**.
- Upstream catalogues may be unavailable, stale, incomplete, or differently
  versioned. Availability, ordering and version labels never establish textual
  equivalence, authorization or suitability for publication.
- An edition already curated in the repository must be improved through its
  approved original and cleaned OSIS master, not replaced by a newer stock
  SWORD module or an automatic preferred-provider selection.

## Curated publication identity gate

Every `approved` resource manifest must carry a stable
`canonical_edition_id` independent of the provider and SWORD module ID.
The publisher must refuse two approved modules with the same canonical ID
**and edition variant** (`faithful` or `reader_optimized`), even when
their module IDs differ. Explicitly reviewed faithful and reader-optimized
variants may coexist; they are editorial variants, not duplicate upstream
imports.

Canonical IDs must be created from verified work, language and edition
identity; never derive them from unverified titles. The publication
schema/validator catches **declared** duplicate IDs, but cannot prove a curator
has not mistakenly assigned distinct IDs to the same edition. New import
reviews must therefore compare the candidate with all approved editions
before owner approval. Record uncertain cases as blocked rather than
introducing guessed identity equivalences.

## Source discovery versus production

The read-only upstream checker (`scripts/check_updates.py`) and
`scripts/check_provider_parity.py` monitor catalogue metadata, upstream
version changes and application-provider declarations. They do not select an
automatic preferred SWORD importer, download Bible texts, grant rights, alter
approved OSIS or authorize release.

The sole production contract is
[`PRODUCTION_PIPELINE.md`](../PRODUCTION_PIPELINE.md): pin original source,
review any cleaned OSIS transformations, independently validate full
source/native text, notes, structure and versification, and obtain explicit
editorial and publication approval before distribution.
