# Historical tools — reproducible evidence, not default production

These tools are retained for source-pinned historical experiments and exact release reconstruction. They are **not** the preferred new-resource OSIS/USFM pipeline; start with [the canonical production contract](../../docs/PRODUCTION_PIPELINE.md) and existing generic intake/validation tools.

## Migration rules

- Move only after enumerating Python imports, workflows, tests, shell commands, docs, release tags and recovery recipes.
- **No root-level compatibility stub or symlink:** update all verified callers to the new path; verify standalone execution and imports.
- Preserve original script contents and effects except the minimum import-path adjustment necessary for relocation; prove test and CI parity.
- Keep the generated [tool registry](../../docs/TOOL_REGISTRY.md) synchronized using `python scripts/tool_registry.py --write` and `--check`.
- Never move a historically used release tool unless published payload bytes and replay capability can be shown unchanged.
- Move no resource prose, OSIS/SWORD data, release provenance or BSI data in a tooling-layout PR.

## Organized historical research

- [LSG source/SWORD research](lsg/README.md) — source/reader text diagnostic and synthetic versification probe with CI coverage.

**Current migration scope:** source-bound LSG probes with direct workflow and test callers. A Darby migration is deferred until its legacy private preflight baseline can be independently verified. Other historical candidates remain at their former paths until separately validated under [issue #430](https://github.com/icfmp/Bible-Resources/issues/430).
