# Architecture maintenance guardrails

**Purpose:** prevent drift after the 2026-11 repository cleanup. These are
ongoing, *generic* engineering rules, not a substitute for editorial,
licensing, content comparison or release approval.

## Keep one authoritative place for each responsibility

| Material | Current home | Not permitted |
| --- | --- | --- |
| Unchanged source and provenance | `sources/original/<type>/<language>/<edition>/` | Patching original bytes |
| Reviewed master and edition evidence | `sources/cleaned/<type>/<language>/<edition>/`, `editorial/` | Shadow masters and undocumented changes |
| Native SWORD payload and metadata | `modules/<edition>/` | Repacking signed releases for tidiness |
| General production/verification tools | `scripts/` | One-off per-verse utilities and alternate publishers |
| Active source/release settings | `config/` | Unused copies of old run configurations |
| Behavior and failure contracts | `tests/` | Tests that merely assert old files were deleted |
| Durable cross-resource guidance | `docs/` | Logs, draft snapshots and transient status reports |
| Generated current tooling inventory | `reports/tooling/` | Unbounded accumulation of debugging outputs |
| Work in progress | Short-lived Git branch and ignored local scratch | A committed `work/`, `history/` or `examples/` tree |

Use official OSIS, USFM/USFX and SWORD conventions as applicable. A
new top-level directory requires an explicit architecture review and
the corresponding guardrail update. That is a deliberate decision,
not a bypass for a particular resource.

## Change protocol

Before adding **a script**: establish a real consumer, search the existing
tool inventory for reusable behavior, document an actual input/output/error
contract and add positive and fail-closed tests. Update the source-bound
script registry through its existing generator. Retire superseded
tools and their callers in the same PR, or state the exact open dependency.
A format-neutral helper belongs in the shared library; edition-specific
decisions belong in data and editorial evidence. Exception code solely to
satisfy one test is not acceptable.

Before adding **a configuration**: identify the live consumer and
schema/validation contract, explain why an existing configuration is
insufficient, and validate all active file references. Never rewrite
immutable release hashes, original provenance or editorial receipts
to satisfy cosmetic layout conventions. Keep historical bindings only
when they are needed for an actual published edition.

Before adding **documentation**: choose the appropriate existing page.
Put a change history in the PR/issue, not a new permanent `FINAL_V2`
report. Edition-specific, approved evidence goes into that edition's
`editorial/`; only reusable procedures go into `docs/`. Update
existing pages when interfaces change, and remove obsolete pointers.

For **every PR**: identify the changed contracts and affected consumers;
state before/after tests, source/editorial/rights effects, remaining
uncertainty and rollback plan. New resource imports must separately
prove exact edition identity, original/source hashes, rights, structural
and semantic fidelity, native SWORD readback and reader compatibility.
A green CI result never authorizes editorial changes or publication.

## Automatically enforced

The [architecture guardrails workflow](../../.github/workflows/architecture-guardrails.yml)
runs on every PR, on `main` and weekly. It checks:

- Approved top-level layout, absence of tracked disposable directories
  and placeholder files, source edition layout and cleaned OSIS manifests.
- Valid JSON configuration objects and existing **explicit active path
  fields**. It does not infer that every configuration has a live
  caller; the PR reviewer must verify that separately.
- Literal active scripts and workflow path-filter references, while
  respecting real glob patterns and explicit historical optional inputs.
- Existing tracked Markdown local links and the pinned script registry.
  Current fidelity, security and release gates still run in
  [Validate](../../.github/workflows/validate.yml).

Tests include synthetic negative cases for the forbidden layout,
missing config references and missing workflow inputs. When a new
legitimate responsibility appears, update the documented policy
and its tests **with the same reviewed change**, not via a hidden
edition-specific workaround.

## Merge controls and limits

The [active `Protect Main` ruleset](https://github.com/icfmp/Bible-Resources/rules/26890406)
was independently read through the GitHub Rulesets API on 2026-11-23.
It requires pull requests, blocks branch deletion and non-fast-forward
updates, and strictly requires the **`validate`** status. There are
no bypass actors. The required Validate job runs the entire unit suite
(including architecture regressions) **and** the source-bound script
registry check, so an error in either prevents merging through the
enforced status gate.

The separate always-running **Architecture guardrails** status is
useful for fast diagnostics and weekly monitoring. It is **not yet**
a required status in that ruleset. The path-filtered legacy registry
maintenance job should not be marked as required without removing its
path filter; the required Validate job independently guards that registry.

**Administrator improvement still pending:** the current ruleset has
`required_approving_review_count: 0`. For mandatory human code review,
set this to at least one and consider adding the always-running
`Architecture guardrails` status as a second required context under
Settings → Rules → Protect Main. The connected GitHub tools can
**read** this ruleset but cannot update its admin settings. CI success
does not imply that the extra review requirement has been enabled.

Do a brief, read-only periodic health check; escalate actual source
drift, unresolved edition errors, or broken published URLs through
their specific issues. Do not delete or repin approved artifacts
automatically.
