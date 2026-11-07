# Publication

Every pull request must pass automated schema and file validation. Human editorial and legal sign-off is required before status changes to approved. Run the tests and `diatheke` smoke check on an actual approved module. GitHub Pages serves the static catalogue and SWORD layout. GitHub Releases or a dedicated storage service may be needed when module size exceeds the Pages budget.


Before changing a module to approved, ensure its original source was checked by a schema-pinned standards validator and the corresponding `SOURCE_VALIDATION.json` exists for the reviewed policy version. A missing or stale report blocks `scripts/validate.py`, and therefore the published catalogue. A source gate result is not itself permission to republish or a proof that a compiled binary round-trips faithfully.


OSIS commentaries require an additional `guard_commentary.py` review of official `annotateType` / `annotateRef` mappings. A successful generic XML/OSIS check does **not** qualify as reviewed commentary source provenance; the commentary-specific policy checksum and annotation proof must match. No source text, embedded Bible quotation, heading, or annotation target may be silently dropped.
