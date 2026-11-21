# BSI shared scripts

Only the source-neutral **entity index** tools live here:

- `compile_index.py` — immutable ACAI source snapshot + audited entity index
- `resolve.py` — source-word and edition-aware candidate resolver
- `distribution_profile.py` — keyterm-free public projection
- `minimal_labels.py` — minimal approved source label selection
- `package_candidate.py` — deterministic candidate archive and manifest
- `audit_person_overlaps.py` — reusable person-word overlap analysis

Regression tests are in [../tests/](../tests/). Source locks, reviewed edits
and exception inventories are in [../data/](../data/); outputs go into
ignored `../dist/`. See [../README.md](../README.md).

UBS Hebrew- and Greek-specific scripts are **not generic**: they are kept
with their pinned dictionary editions in `../links/dictionaries/`.
Never infer a contextual sense or republish source wording from the
presence of a matching lexical ID.
