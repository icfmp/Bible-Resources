# BSI sources — immutable upstream witnesses

This directory **owns source acquisition and provenance**, not editorial changes.

## Pinned witness

- ACAI: `https://github.com/icfmp/ACAI`, immutable revision recorded in [../source.lock.json](../source.lock.json). Its complete **6,644 original JSON records** remain in that historical repository. Do not manually edit, normalize, or duplicate them in the working tree.
- MACULA Hebrew: `https://github.com/Clear-Bible/macula-hebrew`, revision pinned by the same source lock.
- MACULA Greek: `https://github.com/Clear-Bible/macula-greek`, revision pinned by the same source lock.

Run `./bible-semantic-index/sources/checkout-acai.sh` from the repository root to populate `bible-semantic-index/sources/checkouts/acai/` with the exact original revision. This local tree is ignored by Git. The existing source-integrity audit checks both the locked commit and SHA-256 fingerprint of original JSON bytes.

The MACULA TSV witnesses are checked out at their exact revisions by the existing GitHub Actions workflow. No original-language Bible text is bundled in the published BSI ZIP.

**Rights:** the source license is not automatically a license for every upstream third-party component. See [../BSI_V0_1_RIGHTS_AUDIT.md](../BSI_V0_1_RIGHTS_AUDIT.md). Key Terms remain outside the v0.1 distribution.

Do not place generated indexes, editorial decisions, or dictionary links here.
