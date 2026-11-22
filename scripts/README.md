# Script tooling

The `scripts/` directory is for **maintained, reusable production and verification tools**. The active authoring path uses a reviewed OSIS master and independent SWORD/reader checks. Historical one-off probes belong in Git history, not in the current working process.

## Find the right tool

| Location | Role |
| --- | --- |
| `scripts/*.py`, `scripts/*.cpp`, `scripts/*.sh` | Maintained OSIS-first commands, generic validators and independently checked native SWORD tools |
| [`research/bible/`](research/bible/README.md) | Shared strict source-OSIS readers, SWORD markup/verse inspectors and source/native structural evidence; no CLI, source edits or editorial approval |
| `modules/<resource-id>/tools/` | Maintained edition-only diagnostics/replay, never a second publisher; see [Darby](../modules/darby-jnd-2024/tools/README.md) |
| [Generated tool inventory](../reports/tooling/TOOL_REGISTRY.md) | Every tracked tool's classification, source hash, imports and static callers; review evidence, **not** proof that a script is unused |

For a new resource, begin with the [canonical production pipeline](../docs/PRODUCTION_PIPELINE.md). Do not improvise a second importer or add a script for each individual verse or edition correction.

The former MHC and MHCC Modern stock-source reconstruction helpers were retired after their approved OSIS masters were archived under `sources/cleaned/`. The maintained tools validate those masters and their SWORD results; Git history retains the old exploratory code.

## Changing a script

1. **Identify its contract.** Is it an invoked CLI, an imported helper, a read-only probe or immutable historical reproduction? Record exact inputs, outputs, failure behavior and relevant rights/source constraints.
2. **Trace real dependencies.** Inspect Python imports, GitHub Actions, tests, documentation, pinned release/tag callers and external commands. The static inventory is incomplete for dynamic imports or historical revisions.
3. **Prefer consolidation over renaming.** Extract genuinely shared behavior only after demonstrating output equivalence; preserve source- or edition-specific evidence in reviewed manifests, not hardcoded exceptions.
   For import-only Python helpers, update package-qualified imports and their direct tests together; the caller must still place `scripts/` on the Python import path.
4. **Change in bounded batches.** Migrate actual consumers, keep established production entrypoints stable, and avoid compatibility stubs that conceal obsolete paths. Do not relocate a script merely to make the root look emptier.
5. **Verify before merging.** Run `python scripts/tool_registry.py --write` when tracked callers or scripts change, then `--check`, the complete unit suite, source validation, deterministic build, native smoke and relevant real-source/reader workflows. A green test alone never certifies textual fidelity.

## Where a tool belongs

- **Keep in `scripts/`** only a reusable production command, format validator, SWORD reader, or source-neutral research helper with a continuing and demonstrated consumer. A one-time script does not become shared tooling merely because it has its own tests; Git history is sufficient retention unless exact release replay still depends on it.
- **Keep beside a specific resource** only when edition-specific code is still required for a real maintenance, validation or immutable release-replay contract. Prefer reviewed resource manifests and the canonical pipeline over edition-pinned executable copies. Record its real maintenance/replay command with that resource, and review every caller before relocating it.
- **Delete** superseded experiments and finished one-off probes when the canonical process or an existing checked tool covers the needed safeguards. Remove orphan tests, workflows and references together. Git history already preserves the retired implementation; do not maintain duplicate archives or compatibility stubs.
- **Retain historical replay tooling** only when an exact prior published release or source-bound audit still requires it and the replacement has not been proven equivalent. An old one-time release bootstrap that assumes a now-obsolete repository state is *not* an active publisher. Preserve its historical Git revision and immutable release evidence instead of leaving a second, dispatchable publisher on `main`. Before retiring any branch-bound staging job, verify the approved module and release plan exist on `main`; an old checkout that requires the module directory to be absent is not a current publishing path.

For every retirement, record the surviving replacement, currently known callers, any historical replay constraint and the final verification on [#430](https://github.com/icfmp/Bible-Resources/issues/430). No Bible text, approved module payload or editorial ledger may be changed as a side effect.

The active audit and migration tracker is [issue #430](https://github.com/icfmp/Bible-Resources/issues/430). Work on the independent Bible Semantic Index is outside this maintenance scope.
