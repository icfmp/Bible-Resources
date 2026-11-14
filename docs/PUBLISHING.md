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
