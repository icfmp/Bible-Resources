# Upstream contributions

Offer unambiguous bug fixes (encoding, valid references, metadata, OSIS/TEI structural corrections) to CrossWire and original publishers. Submit sources and a reviewable patch/diff, not solely a compiled SWORD binary. Track upstream status and avoid offering reader-optimized editions as faithful technical corrections. The project is independent of CrossWire.

## Provenance when upstream accepts one of our corrections

A fix proposed to CrossWire, STEP or another upstream must retain its upstream
issue/PR URL, exact patch SHA-256 and state: submitted, accepted or released.
**Accepted** is not the same as included in the upstream's binary catalogue.

When a new source version appears, compare its actual content to our last
curated source and saved patch before re-importing. Record a reviewed,
version-specific reconciliation, including source and curated SHA-256,
reviewer and comparison evidence. Only an exact reviewed equivalence warrants
the status \`our_contribution_returned_upstream\`; a change containing our fix
**plus other changes** is still a new review candidate.

Do not apply a patch twice; do not increment \`last_integrated_version\`
unless a version was genuinely imported. For details see
[UPDATES.md](UPDATES.md).
