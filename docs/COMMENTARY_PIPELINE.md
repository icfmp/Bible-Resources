# Reusable commentary pipeline — source first, no invented changes

This is the **commentary** counterpart of the existing
[Bible 7-stage process](BIBLE_7_STAGE_WORKFLOW.md). The stages express
release gates, **not** an artificial deadline or a set of mandatory
one-off helper scripts. Each completed step has a source-bound,
independently reproducible receipt in its GitHub issue. A tool's status
is never a substitute for a source-specific editorial or rights decision.

| Gate | Required evidence | Existing interface |
| --- | --- | --- |
| 1. Discover | Exact author/work/edition, native stock available, redistribution and derivative rights, prior related issues/PRs | `commentary_intake.py --stage 1` |
| 2. Pin original | Immutable upstream ZIP byte count and SHA-256; genuine SWORD ID, version, driver, versification, sample references; optional independent print/digital witnesses *distinguished* | `commentary_intake.py --stage observe` **then** reviewed manifest pin and `--stage 2` |
| 3. Inventory | All original numbered/introduction/opaque entries; authorial sections and references; original source/native XML or ThML markup, without mistaking shared zCom blocks for merged authorial text | `commentary_native_inventory.py`, `commentary_native_raw_inventory.py`; standards-aware native helpers |
| 4. Editorial decision | Classified **data defect vs legitimate editorial choice vs reader-rendering bug**, exact reversible proposed changes, source rights for every addition; no inferred missing verses or redécoupage | Read-only diagnostics, documented correction plans and specific editorial PR |
| 5. Rebuild and compare | Exact original→candidate text/punctuation/notes/refs/section boundaries, all native keys/links, source-hash-bound revision receipt, real SWORD and representative reader | `reviewed_compiled_commentary_rebuild.py` or `compiled_stock_commentary_proof.py` **depending on whether content changed** |
| 6. Approve and package | Human editorial/legal authorization, exact compiled members and SHA-256, immutable version/identity/date, one approved plan and current catalogue, rollback retained | `validate.py`, `release_preflight.py`, `build.py`, `catalogue_release_coverage.py` |
| 7. Publish and verify | Release asset created/verified **before** Pages, HTTPS ZIP/cache verifications, actual installation/navigation/typography and provider migration behavior | `pages.yml`, `verify_public_catalogue.py`; separate app-level UX issue if needed |

## Commands (metadata-only preflight, no release)

For an existing manifest, source observation performs network access but must
**never** be treated as approved redistribution or a source-content proof:

```sh
python scripts/commentary_intake.py --resource-id RESOURCE --stage 1 \
  --report /tmp/commentary-identity.json
python scripts/commentary_intake.py --resource-id RESOURCE --stage observe \
  --report /tmp/commentary-observation.json
# Review and separately pin the exact source archive SHA; do not autopin it.
python scripts/commentary_intake.py --resource-id RESOURCE --stage 2 \
  --report /tmp/commentary-pinned.json
```

Actual checked-in **approved** resources can all use the same offline
source/rights/payload/release proof, without a second packaging implementation:

```sh
python scripts/release_preflight.py \
  --module-id lsg-1910 \
  --module-id darby-jnd-2024 \
  --module-id mhcc-crosswire \
  --report /tmp/verified-sword-packages.json
```

The release preflight simply composes the production gates and reconstructs
the exact deterministic public-plan ZIP **in a temporary directory**. It
does not change the repository, approve a new rights claim, call the GitHub
publishing API or prove UI rendering in every reader. The integration test
covers three **independently attested and already published** real editions:
LSG `RawText`, Darby `zText` and MHCC `zCom`. Their checked-in
source native proofs and rights records remain edition-specific.

## Companion original-compilation audit

The supported original commentary drivers are `RawCom`, `RawCom4`,
`zCom` and `zCom4` only where the actual module and native reader
support them. A reference/entry count is **not** authorial scope parity:
linked verse slots can share one physical commentary body; introductions
and opaque entries must be inventoried separately. Extract source text
only privately where rights permit, using actual standard SWORD tools.
Never invent OSIS markup, citation ranges, or original sections just
to make a tool pass. A reader-rendering bug (such as a double heading)
belongs in the Bible application, not a destructive edit to the module.

The large [historic MHCC scope experiment](
../.github/workflows/commentary-editorial-section-scope.yml) and related
private source/CCEL experiments are evidence for
[the MHCC 0.1.1 decision](
evidence/mhcc-274/mhcc-0.1.1-editorial-rights-acceptance.md), **not** a
generic stable runner or an invitation to rerun 2,000 lines of
edition-specific assertions for a new commentary. Shared helpers may
be reused after independent tests; keep historical workflows for
reproducibility until reviewed migration coverage exists.

### A second independent commentary

The CrossWire public catalogue lists **John Wesley's Notes on the Bible**
as `Wesley` 1.1 (2001-11-28) with a **Public Domain** claim. Its source
description attributes electronic edition/markup work to named editors.
This makes it a useful **private, read-only** cross-commentary
intake/inventory pilot; no edition-equivalence, corrective editing, or
redistribution approval is implied. John Gill should be considered only
after discovering a verified source and separate rights. Unlike MHCC,
a Wesley pilot must exercise the actual driver and native inventory it
offers, not copy MHCC's 28,742-key counts, alias plan, editor or correction
list. If the original ZIP cannot be pinned or independently read, record
`BLOCKED` rather than inventing PASS.

## Error categories and review decisions

Use `DONE` only for a clearly defined completed gate, `PARTIAL` for
demonstrated limited coverage, `BLOCKED` for a real failed prerequisite,
and `INCONCLUSIVE` where source witnesses/readers disagree. Keep report
identity (resource ID, source SHA, code commit, driver, native keys,
exit status, URLs and independent receipts); avoid logging original
licensed prose or notes in public artifacts. A single private observation
can identify a candidate anomaly but can neither rewrite an authorial
passage nor authorize publication.

For scripts and their preserved legacy callers, consult
[the full tool registry](TOOL_REGISTRY.md) and the
[contributor rules](../CONTRIBUTING.md). General packaging and release
checks belong in [PUBLISHING.md](PUBLISHING.md); Bible
translation source/native fidelity stays in #28, and resumable
multi-stage audit orchestration stays in #83 rather than being
reimplemented here.
