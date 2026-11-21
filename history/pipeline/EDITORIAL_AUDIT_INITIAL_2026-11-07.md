# Initial editorial audit observations — 2026-11-07

**Historical evidence only.** These original observations predate subsequent module imports and releases. Consult [the active OSIS editorial audit tooling guide](../../docs/workflows/EDITORIAL_AUDIT_WORKFLOW.md) and [canonical production contract](../../docs/PRODUCTION_PIPELINE.md) for current processes.

## Actual first-source observations (2026-11-07)

Read-only GitHub Actions evidence:
[LSG and MHC structure fingerprints](normalizer-3/real-pilot-source-signals.json).
The exact publisher ZIPs were downloaded into temporary storage and scanned
with key-scoped `diatheke` requests. After correcting an initial flag-order
bug, LSG **Psalm 23 already contains poetry markup signals** and full
MHC **Genesis 1 contains paragraph markup signals**. Do not flatten or
rebuild them merely because the Bible UI looks wrong; verify rendering first.

This is **neither** a complete verse/text identity check nor proof that
every paragraph is correct. No automatic source edits, original MHC OSIS
reconstruction, SWORD recompilation or public resource release has occurred.
Evidence from the earlier accidentally unbounded `diatheke` queries is
explicitly invalidated; only the corrected bounded-reader run is cited.

The OSIS editor cannot work directly on an opaque compiled SWORD archive:
if the original source cannot be obtained, the future extraction adapter
must reconstruct a clearly *generated* intermediate with SWORD entry keys,
never assert that generated lines are original source lines.

See also [the full quality policy](../../docs/policies/QUALITY_POLICY.md), [editorial rules](../../docs/policies/EDITORIAL_RULES.md),
and [pilot issue #12](https://github.com/icfmp/Bible-Resources/issues/12).
