# Publication — one ordered release workflow

**Publishing is one operation, not two independent workflows.** The
[GitHub Pages publication workflow](../.github/workflows/pages.yml)
is the only workflow allowed to **create/verify GitHub Releases and
then expose the same approved modules through Pages**. The previous
independently triggered GitHub Release workflow was removed: its push
trigger allowed an approved module to appear in the catalogue before
a versioned GitHub Release existed.

## Owner authorization and evidence

Human editorial and rights sign-off is required before setting
`quality.status=approved`. Preserve exact-source evidence, authors'
words, all notes/annotations/structural markers, licensing, and the
original-versus-curated SWORD payload provenance. A successful CI result
is not a substitute for this decision.

For rebuilt OSIS sources, require the official version-pinned OSIS
schema and independently verified source-to-SWORD preservation. OSIS
commentaries additionally require validated commentary annotations.
For **unchanged, compiled upstream SWORD stock**, require the separate
full original compiled-data/native-entry identity proof; do not
fabricate a source OSIS document just to satisfy an XML gate.

## Source-corrected compiled SWORD commentaries

An edited or reconstructed `zCom` is **not** original-stock SWORD data.
It must never be validated through `stock_reader_keys`, which keeps
requiring exact original CrossWire compressed-member and native-entry identity.

The separate `reviewed_compiled_commentary_rebuild` route requires a
**versioned, independently reviewed** original-source identity,
complete libSWORD original-to-rebuilt native I/K/TOP comparison,
explicit per-source correction and alias sets, an immutable SHA-256
of that comparison report, and exact SHA-256s of all seven SWORD payload
members (six zCom data files and one `.conf`). The module's
`SOURCE_VALIDATION.json` must reference that same independent report
and source review. A build that merely sets `validated=true` is rejected.

**Architecture decision (2026-11-16):** the project owner delegated
this technical choice and the two separate routes are adopted. This does
not authorize a particular source correction for public release, a merged PR
or any public artifact. Independent proof and release gates remain required.

The offline validator binds the submitted proofs and actual packaged bytes;
it **does not itself execute libSWORD or authenticate a human signature**.
Prior to editorial approval, independently regenerate and review the complete
native comparison from the SHA-pinned source and real candidate, and confirm
the GitHub authorization record genuinely comes from the project owner.
See [generic proof contract](evidence/mhcc-274/rebuilt-commentary-validation-contract.md).
A synthetic passing unit test does not authorize publication.

## Upgrading an existing approved commentary without losing its old release

There is **one current version per stable module identity** in the catalogue.
For a source-corrected successor, retain the existing module directory,
curated module ID, SWORD ID and canonical source-edition lineage. Update its
version, actual verified SWORD payload, metadata and source-specific proof
only after the corresponding source/rights decision. Never install a second
approved module with a duplicate SWORD identity beside the original.

There is likewise **one active release plan per current module ID**. For
BRMHCC 0.1.1 the eventual authorized change must **replace**
`config/release-plans/mhcc-0.1.0.json` with a new
`config/release-plans/mhcc-0.1.1.json`. Do not keep both active; the coverage
gate deliberately rejects duplicate plans. This does **not** modify, delete
or repurpose the already published and immutable GitHub Release
`mhcc-0.1.0` or its ZIP. Its original approved plan remains in Git history.
Before the new release, independently re-download and verify the 0.1.0
release checksum as an explicit rollback specimen.

An approved descriptive profile is **specific to an exact module version**.
The current MHCC `profiles/en.json` is for 0.1.0 and states that no source
words or references were modified; reusing it for 0.1.1 would be false.
The profile validator rejects the version mismatch. Either obtain a new
owner-approved, source-hash-pinned 0.1.1 profile with accurate changes and
rights, or remove the **optional** profile from the new current catalogue
until a fresh profile has been approved. Never re-pin the old profile merely
to silence validation. A [separate, unapproved new-profile draft](
evidence/mhcc-274/0.1.1-reader-profile-DRAFT.md) is prepared for review.

After editorial/legal approval, the current single catalogue row for
`mhcc-crosswire` can switch to version 0.1.1 and its new stable
`sword/packages/BRMHCC.zip` checksum. A separately authorized new immutable
GitHub Release must be created and verified **before** Pages advertises
the new ZIP. The previous 0.1.0 GitHub Release remains available, while
the stable Pages path intentionally points to the current approved version.
No existing user installation, settings, notes or application-side rollback
is changed by this repository.

## Mandatory publication contract

Every **approved** catalogue entry must have exactly one documented
versioned GitHub Release path:

- **New or updated module:** an authorized,
  [source-pinned release plan](../config/release-plans/)
  for the *same* module ID, version, exact deterministic SWORD ZIP
  SHA-256 and byte length as the official JSON catalogue. The existing
  source/rights/approval evidence must pass
  `scripts/publish_reviewed_release.py --verify-only`.
- **Previously published module:** a frozen,
  [reviewed historical binding](../config/release-legacy-bindings.json)
  with the original GitHub Release tag/asset and independently pinned
  release and catalogue checksums. This is a historical migration
  record, **not permission to use exceptions for new modules**.
  A difference between historical GitHub and Pages ZIPs is disclosed,
  not silently treated as source equivalence.

Neither a published `mods.d` archive nor a successful local build
counts as a GitHub Release.

A pull request must pass [Validate](../.github/workflows/validate.yml),
including the exact local mapping of all approved catalogue entries
to their release plans, the generated ZIP checksums and a read-only
review of every current release authorization. A newly approved
module without an authorized release plan **fails CI**.

## Single workflow on main

On a reviewed merge to `main`:

1. Install dependencies, run unit tests, validate all module metadata,
   source and original licence proofs, build the deterministic catalogue
   and packages, and run a real `diatheke` smoke test.
2. Verify **complete** plan/legacy coverage for every approved
   resource with `scripts/catalogue_release_coverage.py --built dist`.
3. Using approved manifest(s), check each historical GitHub Release
   by **actually downloading** its pinned versioned ZIP, byte length
   and SHA-256. Then create or verify each current versioned GitHub
   Release, and **download** its asset to confirm exact identity with
   the deterministic catalogue ZIP. Existing release tags/assets are
   never overwritten. This step must succeed **before Pages upload**.
4. Only then upload and deploy the Pages catalogue and standard
   `mods.d/`, `modules/` and `sword/packages/` layout.
5. Independently download the public HTTPS catalogue and every
   advertised Pages ZIP; verify their exact SHA-256 and sizes with
   `scripts/verify_public_catalogue.py`. A failed HTTP verification
   is a **failed publication check**, not a false success.

This order prevents the observed failure mode **catalogue visible,
GitHub Release absent**. It is not a literal distributed database
transaction: GitHub Release creation can succeed and a later Pages
deployment can fail. In that case the existing Pages catalogue
remains unchanged until the deployment succeeds; rerunning the
workflow safely verifies existing versioned assets without replacing
them.

Manual GitHub Pages deployments must use the same release gates,
on `main` only. No third-party reader certification is implied.

## Historical Segond packaging caveat

The existing **Louis Segond 0.1.0** versioned GitHub Release
(`BRLSG1910-0.1.0.zip`, SHA-256
`af2f80ea84f40a6bf62993c9e65c2e2061e1ec20b34b0772a4eb775dd47723c1`)
and its current Pages catalogue ZIP (`BRLSG1910.zip`, SHA-256
`f3f74a1016f708e10263b5628e606a73b727c0e80fbb7e131d195c4b11d86c51`)
have **different bytes and lengths**. Both are pinned and must be
verified separately as part of the historical transition. This
does **not** prove an authorial difference, nor does it prove exact
native-data equality. Do not silently replace the released 0.1.0
asset, or claim the two packages are identical without separately
auditing their content, metadata and source/compiled identity. A
future source-grounded update requires its own issue and approval.

By contrast, the current approved **Darby 0.1.1** archive and its
versioned GitHub asset have the same pinned ZIP checksum. **MHCC
0.1.0** uses the strict identical-bytes, current release-plan path.
