# Cross-repository architecture audit — 2026-11-23

**Baseline:** [main `0602f5ecfdd0f18d5587adfc0f73db32048f33cd`](https://github.com/icfmp/Bible-Resources/commit/0602f5ecfdd0f18d5587adfc0f73db32048f33cd). **Verdict:** the active source-first architecture and release paths are coherent. This is **not** a new independent semantic or printed-edition collation.

## Verified active inventory

| Scope | Observed |
| --- | ---: |
| Git-tracked regular files | 344 |
| Tracked `work/` files | 0 |
| Reviewed cleaned OSIS masters | 5 |
| Approved SWORD modules and current catalogue entries | 5 / 5 |
| Public non-draft versioned SWORD ZIP Releases | 5 |
| GitHub Actions workflows | 10 |
| Registered tools / Python test files | 49 / 46 |

The current five editions are **LSG 0.1.0**, **Darby 0.1.1**,
**MHCC classic 0.1.1**, **MHC complete 0.1.0** and
**HMCC Modern 0.1.0**. Three have current reviewed release plans;
LSG and Darby use explicit frozen historical release bindings.
Every current edition has a cleaned OSIS master. Original sources,
rights, manifests, publication metadata and approved source hashes
remain distinct: reconstruction is not evidence that an original
publisher-authored OSIS was recovered.

## Scope and results

- Inspected the complete non-truncated Git tree, ten active workflows,
  maintained scripts and their checked-in registry. No current
  script/workflow requires `work/` or a deleted production entrypoint.
  The already published HMCC Modern `.conf` historical `TextSource`
  and historic provenance records deliberately retain the old URL;
  original authoring Markdown is recoverable at immutable Git commit
  `c96bebf42d8e0eba62fa961f7f16a00806a50e2c`.
- Screened all 43 baseline `docs/` files and main entrypoint
  Markdown for local link destinations; no broken targets identified.
  The checked-in Markdown link regression also verifies approved
  signed-profile blob exceptions independently.
- Confirmed the four active HMCC Modern owner-decision/anomaly JSON
  inputs under its `sources/cleaned/**/editorial/evidence/` have
  **unchanged Git blob identities** after relocation; the release
  validator uses the edition-owned paths.
- [Main Validate #45087492069](https://github.com/icfmp/Bible-Resources/actions/runs/45087492069)
  and [Publish/Pages #45087492270](https://github.com/icfmp/Bible-Resources/actions/runs/45087492270)
  both completed **SUCCESS**. The preceding refactor PR passed
  **402 Python tests** and the script-registry guard. The publishing
  workflow checks public catalogue/package delivery; the present audit
  did not separately re-download every public ZIP.
- Closed obsolete staging [PR #386](https://github.com/icfmp/Bible-Resources/pull/386)
  **unmerged**, because MHC 0.1.0 is already published with its
  versioned release asset and approved master. The staging evidence
  remains available historically.

## Residual risks; not resolved by structural cleanup

- [#517](https://github.com/icfmp/Bible-Resources/issues/517):
  old GitHub API-tree versus clean Actions checkout mismatch for an
  owner-decision witness has no fully demonstrated root cause.
  The current relocated path passes clean CI, but the historical
  discrepancy remains a separate investigation.
- [#487](https://github.com/icfmp/Bible-Resources/issues/487)
  and [#452](https://github.com/icfmp/Bible-Resources/issues/452):
  observed upstream original-archive SHA drift. No silent repinning.
- [#271](https://github.com/icfmp/Bible-Resources/issues/271):
  historical Segond GitHub Release versus Pages ZIP disparity.
  Frozen source-specific hashes must stay distinguishable.
- [#95](https://github.com/icfmp/Bible-Resources/issues/95),
  [#274](https://github.com/icfmp/Bible-Resources/issues/274),
  and other original-text/editorial issues remain open; do not claim
  complete semantic, notes or reader fidelity from a green build.
- [#28](https://github.com/icfmp/Bible-Resources/issues/28),
  [#83](https://github.com/icfmp/Bible-Resources/issues/83)
  and [BRNP #451](https://github.com/icfmp/Bible-Resources/issues/451)
  track future generalized fidelity, resumable evidence and
  normalization conformance work.
- [#270](https://github.com/icfmp/Bible-Resources/issues/270)
  remains open despite HMCC Modern publication: separate historical
  draft-era claims from outstanding editorial/GUI follow-up before
  closing; publication does not retroactively validate every click.

**Disposition:** the tracked-directory cleanup and source-first
structural rearchitecture are complete. Continue source, rights and
reader investigations through the relevant edition issues, rather
than creating a permanent staging directory or a second publisher.
