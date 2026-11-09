# Stable SWORD reference-index audit integration

The reusable, source-independent `scripts/stable_sword_refs.py` and synthetic regression suites were recovered from [historical PR #23](https://github.com/icfmp/Bible-Resources/pull/23).

## Current status

- The generic audit logic and two regression suites are available for inspection and testing.
- **This stage does not yet make the audit a mandatory release gate.** `scripts/validate.py` is intentionally unchanged. The already-published LSG 0.1.0 lacks the audit's `SWORD_COMPATIBILITY.json` and `SOURCE_REFERENCE_MERGES.json` receipts. Adding an unconditional import/call would reject the published catalogue without independently reproducing those proofs.
- No release artifacts, existing module payloads, Scripture, or their approved hashes are modified.

## Mandatory follow-on before claiming full integration

1. Generate the complete independent text-free authorial-source, stock-reader and released-SWORD registry key inventories for the exact published LSG payload. Pin SWORD engine version and original/source/payload digests, using audited sources rather than copying claimed values.
2. Reconcile existing approved Mark 10:52–53 merge evidence with the required source-bound policy, full original chapter body readback and exact compiled bytes. Do not use a hardcoded LSG exception, synthetic proof or `PENDING` reviewer.
3. Attach independently reviewed and reproducible `SWORD_COMPATIBILITY.json` for LSG; verify corrupt/missing/stale reports block, including the authorized merge and an unapproved adjacent merge.
4. Wire `stable_sword_refs.proof_errors` into the generic approved Bible validation path and confirm the existing LSG catalogue rebuild, validation and Pages deployment remain green. Test a second actual edition before claiming cross-translation proven.
5. Document the machine-generated audit recipe and limitations. Reference [issue #28](https://github.com/icfmp/Bible-Resources/issues/28).

The numerical reference-index audit is **not** proof of textual, note, typography, or frontend fidelity. Published 0.1.0 editorial approval remains separate.
