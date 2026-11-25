# Registered USFM conversion (private candidate)

This workflow is separate from approved edition cleaning and publication.

1. Register immutable USFM and independent USFX witnesses, exact member, reviewed crosswalk and provenance. This route supports only grammar handled by the existing independent comparators; it fails on unsupported constructs.
2. Retrieve the reviewed public-domain u2o revision `dde28bc545e8d8697fa5496c243187847ec55d31` and use `python scripts/fetch_reviewed_schema.py --directory /tmp/osis-schema`.
3. Run `python scripts/convert_usfm.py --resource RESOURCE --converter /tmp/u2o.py --schema /tmp/osis-schema/osisCore.2.1.1-cw-latest.xsd --source-date-epoch EPOCH --output /tmp/new.osis.xml --report /tmp/new.json`. Use an explicit immutable input timestamp, not the current clock. Use a pinned Python runtime and exact inputs to reproduce bytes.
4. Review the metadata-only receipt. The candidate preserves supported source semantics, not editorially reviewed target destinations. Existing approved repairs and release-specific authorizations must be applied separately with their independent proofs. Do not overwrite originals or approved masters.

The command does not compile, change source bytes, infer rights, or publish.
The conversion research branch is not an approved release pipeline.
