# Script tooling

The `scripts/` directory contains **production commands**, reusable libraries, independent research probes and historical reproduction tools. Their status is determined by tested callers and source evidence, not by filename or location.

## Find the right tool

| Location | Role |
| --- | --- |
| `scripts/*.py`, `scripts/*.cpp`, `scripts/*.sh` | Existing production entrypoints, shared validators, native inspectors and research commands whose callers have not yet been migrated |
| [`research/commentary/`](research/commentary/README.md) | Non-CLI, read-only commentary chapter, section, introduction, paragraph and native-scope diagnostics; **not** publication or editorial approval |
| [`historical/`](historical/README.md) | Source-pinned reproduction of older decisions and modules; preserve exact inputs and existing historical tests |
| [Generated tool inventory](../reports/tooling/TOOL_REGISTRY.md) | Every tracked tool's classification, source hash, imports and static callers; review evidence, **not** proof that a script is unused |

For a new resource, begin with the [canonical production pipeline](../docs/PRODUCTION_PIPELINE.md). Do not improvise a second importer or add a script for each individual verse or edition correction.

## Changing a script

1. **Identify its contract.** Is it an invoked CLI, an imported helper, a read-only probe or immutable historical reproduction? Record exact inputs, outputs, failure behavior and relevant rights/source constraints.
2. **Trace real dependencies.** Inspect Python imports, GitHub Actions, tests, documentation, pinned release/tag callers and external commands. The static inventory is incomplete for dynamic imports or historical revisions.
3. **Prefer consolidation over renaming.** Extract genuinely shared behavior only after demonstrating output equivalence; preserve source- or edition-specific evidence in reviewed manifests, not hardcoded exceptions.
   For import-only Python helpers, update package-qualified imports and their direct tests together; the caller must still place `scripts/` on the Python import path.
4. **Change in bounded batches.** Migrate actual consumers, keep established production entrypoints stable, and avoid compatibility stubs that conceal obsolete paths. Do not relocate a script merely to make the root look emptier.
5. **Verify before merging.** Run `python scripts/tool_registry.py --write` when tracked callers or scripts change, then `--check`, the complete unit suite, source validation, deterministic build, native smoke and relevant real-source/reader workflows. A green test alone never certifies textual fidelity.

The active audit and migration tracker is [issue #430](https://github.com/icfmp/Bible-Resources/issues/430). Work on the independent Bible Semantic Index is outside this maintenance scope.
