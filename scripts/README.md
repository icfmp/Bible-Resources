# Executable tooling — lifecycle and maintenance

Keep stable script paths as public interfaces until their **actual** Python
imports, tests, CI workflows, external documented commands, and historical
release consumers are all verified. Moving a script can silently break
source-bound evidence even when it looks like a minor directory tidy-up.

The generated [tool inventory](../docs/TOOL_REGISTRY.md) and its JSON
counterpart are the canonical per-script index, with documented lifecycle
categories: KEEP_GENERIC, GENERALIZE, MERGE, HISTORICAL/ARCHIVE, UNDECIDED.

**Production:** extend existing generic intake, OSIS normalization, USFM
support, source parity, reference validation, SWORD build and reader checks.
Use the standard six-phase pipeline; avoid new program-per-resource scripts.

**Research:** historical one-off readers/probes may be kept for replay, but
are not the preferred production pipeline. Relocate only after the real
workflow/caller/test/historical-tag audit and behavior-equivalence proof.

**No cosmetic mass move:** this workspace cleanup deliberately leaves
original script locations callable. Classifications alone do not prove
that a file is dead code; the nine historical/archivable flags have active
script, test or workflow references. Reorganization is not an authorization
to delete or silently change their outputs.

[Canonical workspace paths](../docs/WORKSPACE_LAYOUT.md).
