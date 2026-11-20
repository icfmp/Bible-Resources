# Bible Resources documentation

**Start here if you are new to the repository.** Bible Resources preserves, verifies and distributes source-faithful SWORD resources. A successful build is not proof of textual fidelity, a license to redistribute, or an approved release.

## Your first five minutes

1. Read [the architecture](architecture/ARCHITECTURE.md): what is original, what can be edited, what is compiled, and what gets published.
2. Read [the production pipeline](PRODUCTION_PIPELINE.md): the **single** end-to-end procedure and the evidence required to advance.
3. Study the [BRNP structural profile](architecture/BRNP.md) for our proposed common OSIS representation (pilot; not a release gate yet).
4. Check [editorial and legal policies](policies/README.md) before touching content.
5. Choose [a workflow](workflows/README.md) for a Bible, commentary, technical audit or release.
6. Consult [verification methods](technical/README.md) only when performing a corresponding check.

## Where to find things

| Looking for | Go to |
| --- | --- |
| Source download and original identity | `sources/original/<type>/<language>/<id>/` and provenance records |
| Cleaned editorial master, exact decisions and audits | `sources/cleaned/<type>/<language>/<id>/editorial/` |
| Generic project design and directory conventions | [architecture](architecture/README.md) |
| Rules for fidelity, rights, versification and changes | [policies](policies/README.md) |
| How to execute a production or release step | [workflows](workflows/README.md) |
| How to inspect OSIS, SWORD, notes, references or rendering | [technical methods](technical/README.md) |
| Current priorities, blockers and actual progress | GitHub issues, PRs, Actions and approved edition manifests |
| Older cross-cutting experiments retained for provenance | `history/` — never treat these as instructions |
| Compiled modules and distribution outputs | `modules/`, `sword/`, `catalog/v1/` |

## A concrete way to contribute

Choose an existing issue before starting duplicate work. Pin the exact source, edition, rights and hash. Keep the original immutable; work on a separate cleaned candidate. Produce an exhaustive source-to-candidate diff, document every approved transformation, and test the compiled module independently. Do not publish without explicit editorial, rights and release approval. Record a resumable checkpoint in the issue, referencing commits and actual test runs.

Do not confuse **source defect**, **editorial convention**, **compiler/index behavior**, and **reader rendering defect**. A workaround for a particular client does not justify rewriting the author's text.

## Documentation maintenance rule

Keep `docs/` short and durable. Document a reusable rule **once**, at its most natural home, with links from entry points. Remove superseded explanations rather than accumulating variants. Place dated tests and module-specific history with the module; preserve cross-project research in `history/` only when its evidence is useful. Do not add execution logs or lists of temporary PR results to general guides.

`entity-index/` is the separate Bible Semantic Index workstream: do not touch it during documentation housekeeping.
