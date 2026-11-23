# Architecture

Read [architecture](ARCHITECTURE.md) to understand **what is authoritative** and where the boundaries between original, edited and compiled data lie. Read [workspace layout](WORKSPACE_LAYOUT.md) when adding or locating files.

The [maintenance guardrails](MAINTENANCE_GUARDRAILS.md) define the permanent boundaries for tools, configurations, documentation and CI checks. They are enforced on each PR and checked weekly.

The [BRNP proposal](BRNP.md) records a deferred plan for common source-preserving structure; it is **not** a release gate. Additional architecture references are [supported formats](FORMATS.md) and [resource profile contract](RESOURCE_PROFILES.md).

For how to process an edition, go to the [production pipeline](../PRODUCTION_PIPELINE.md). For edition-specific decisions and evidence, go directly to its `sources/cleaned/**/editorial/` directory. BSI development now lives in the [independent Bible Semantic Index repository](https://github.com/icfmp/Bible-Resources-Semantic-Index); it is outside the resource production pipeline.
