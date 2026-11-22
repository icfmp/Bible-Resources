# Maintained script retention audit — 2026-11-22

Scope: the **49 tracked tools** in the generated tooling inventory after
cleanup #510. This is a maintenance lifecycle review, **not** approval of
a textual transformation, a release, or a claim that CI tests prove editorial
fidelity. The historical baseline for this cleanup was 160 tools.

## Decision rule

An active, independently useful check is retained even if its original
development task is complete. Static reference counts alone never justify
deletion. A command remains active only when its current caller, import
dependency, release replay requirement or documented reusable manual
purpose can be established.

The registry deliberately separates three decisions:

- **23 core entrypoints/validators**: previously reviewed stable interfaces,
  relied upon by the OSIS-first intake, validation, release, commentary or
  native SWORD checks (high classification confidence).
- **25 actively retained, not-core tools**: manual source-neutral editorial
  inspection, provenance/edition and catalogue checks, a used legacy release
  evidence adapter, the package-owned source/native analysis libraries,
  native SWORD forensic readers and source-bound readback. Their ongoing
  consumers are in the registry. These have **medium**, not high,
  classification confidence; future refactoring still requires output parity.
- **1 still edition-coupled validator**: the *modern commentary release
  evidence gate* binds to source decisions and review counts specific to the
  approved HMCC Modern edition. It is actively called by the shared
  validator and may **not** be removed or treated as an interchangeable
  commentary proof until a data-driven replacement is independently
  demonstrated.

The remaining tools therefore have no unresolved *retention decision*, but
the edition-coupled gate still has a *design improvement* pending. We do not
move it into module-local code through dynamic imports: a shared release
validator must never execute an unreviewed module-supplied script.

## Confirmed shared responsibilities

| Function | Continued responsibility | Key evidence |
| --- | --- | --- |
| Original intake and acquisition | Reviewed Bible/commentary intake and safe bounded original source observations | Intake workflow, archive and reader tests |
| OSIS diagnostics | Read-only structural screening, source inventory, source→candidate semantic fidelity, exact reviewed XSD checks | Direct offline tests and editorial workflow |
| Canonical release | Validated source/master, duplicate-edition identity, archive integrity, generated catalogues and public coverage | Release preflight, validate and publishing workflow |
| SWORD forensic comparison | Independent native index/corpus readers, verse/note/structure/intro-title addressability and bounded binary inspection | Approved OSIS-native audit and native corpus CI |
| Reader availability | Actual diatheke smoke on approved published modules | Validate CI and its reader smoke |
| Commentary evidence | Distinct stock, source-attested rebuilt, historical-OSIS and modern derivative gates | Approved metadata and release evidence from actual MHC/MHCC/HMCC Modern modules |
| Tool lifecycle | Static provenance, source hash, caller and build-target evidence | Tool registry consistency CI |

All source/native helper modules stay in the existing shared research package,
not duplicated per Bible edition. The source-neutral semantic fidelity CLI
is retained as a read-only manual validation tool even though it has no
always-on workflow; its direct tests and the editorial procedure document
its invocation contract.

## Explicitly rejected cleanups

- Do **not** delete old-release reference adapters while approved published
  modules still select those evidence modes.
- Do **not** turn a modern-English derivative's editorial decisions into
  generic text-rewrite rules or accept its attestation as source-text identity.
- Do **not** remove the historical compiler reproducibility witness used to
  preserve source-authored testament headings in the approved Darby OSIS.
- Do **not** eliminate independent native reader evidence to make the
  implementation count smaller.
- Do **not** classify a parser, test fixture or SWORD reader merely by its
  filename; verify its exact contract and run all relevant real-source tests.

## First safe shared binary format extraction

The approved compiled and modernized commentary release validators now share
the **same** deterministic native zCom member layout definition, including
BOOK, CHAPTER and VERSE compression granularities, safe SWORD identifiers
and the seven expected payload paths. Both gates also share fail-closed inventory
checks for missing, extra and symlinked payload members. The modern release still authenticates
the actual bytes against its independently approved artifact hashes.

This is *technical code consolidation*, not a rewrite of the modern-English
editorial proof. All edition-specific link corrections, restorations,
authorizations and SHA-256 evidence remain frozen and are **not** inferred
from a generic validator or revised on the basis of the format helper.

## Next maintenance boundary

Further reduction now requires a **proved functional consolidation**:
compatible inputs, identical outputs/diagnostic failure behavior, verified
source and native data on real resources, updated callers and successful
reproducible release audits. The modern commentary proof gate is the clearest
remaining candidate for data-driven generalization, subject to preserving its
reviewed edition-specific decisions and independent authorization.

No Scripture bytes, source master, notes, verse numbering, licences or published
SWORD payload are modified by this retention review.
