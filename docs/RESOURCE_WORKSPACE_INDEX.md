# Current resource workspace index

This is a **navigation index**, not an additional source of truth for edition
rights, authorial text or publication approval. The authoritative identifiers
and status are in each resource's `modules/<id>/metadata.json` and the
current catalogue. The [typed workspace convention](WORKSPACE_LAYOUT.md)
applies to all new source and work files.

## Bibles

| Resource | Authoritative existing metadata | Original source | Maintained source |
| --- | --- | --- | --- |
| Louis Segond 1910 (`lsg-1910`) | [Metadata](../modules/lsg-1910/metadata.json) | eBible edition/revision pinned in metadata and source-audit receipts; original USFM/USFX **not mirrored in the new source tree** | No standalone OSIS/USFM body currently committed in the new typed source tree; reviewed SWORD and audits live under `modules/lsg-1910/` |
| Darby (`darby-jnd-2024`) | [Metadata](../modules/darby-jnd-2024/metadata.json) | Exact original pinned in resource provenance; no assumption that downloaded text may be mirrored | Reviewed SWORD, cleanup audit and receipts currently under `modules/darby-jnd-2024/` |

## Commentaries

| Resource | Authoritative existing metadata | Original source | Maintained source and work |
| --- | --- | --- | --- |
| Matthew Henry Complete (`mhc-crosswire`) | [Metadata](../modules/mhc-crosswire/metadata.json) | Original CrossWire OSIS identified and hash-pinned in [MHC source record](../sources/cleaned/mhc/README.md), **not mirrored here** | [Historical MHC provenance](../sources/cleaned/mhc/README.md); no committed full clean OSIS file; [MHC CCEL research archive](../work/commentaries/mhc-crosswire/experiments/ccel-imp/README.md) |
| Matthew Henry Concise (`mhcc-crosswire`) | [Metadata](../modules/mhcc-crosswire/metadata.json) | Original CrossWire witness documented in release/rights evidence | Compiled reviewed SWORD and exact source/native integrity receipts under `modules/mhcc-crosswire/` |
| Henry's Modern Concise Commentary (`hmcc-modern`) | [Metadata](../modules/hmcc-modern/metadata.json) | Modern edition has **its own** copyright/permissions separate from Henry's public-domain historical prose | [HMCC Modern historical manuscript/archive index](../work/commentaries/hmcc-modern/README.md), pointing to original SHA-/source-bound paths under `work/mhcc-modern/`. Validated published payload remains under `modules/hmcc-modern/` |

## Other resource types

`dictionaries/`, `encyclopedias/` and `other/` are now reserved and
ready for **actual** authorized original and maintained source files. No
fictional completed ingestion is implied by empty category folders. Shared
Biblical entity/index datasets continue to use their existing independent
`entity-index/` paths; they are **not** automatically source texts or
encyclopedia editions. Do not move the concurrently active UBS project
through this resource-workspace cleanup.

## Important distinction

- `sources/original/<type>/<id>/`: immutable real original, if rights allow
  mirroring, otherwise a reliable provenance reference only.
- `sources/cleaned/<type>/<id>/`: actual reviewed editable OSIS/USFM master
  when one has been produced and may be stored. **A SWORD payload is not a
  cleaned authorial source.**
- `work/<type>/<id>/`: drafts, historical source collation and test
  evidence.
- `modules/<id>/`: standard SWORD distribution and immutable release proof.
- `scripts/`: stable tool interfaces; [tool lifecycle registry](TOOL_REGISTRY.md).

See [source-first production policy](SOURCE_FIRST_EDITORIAL_PIPELINE.md)
for Strong, morphology, translation notes, references, provenance, Xiphos
tests and publication gates.
