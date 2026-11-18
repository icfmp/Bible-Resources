# Reusable commentary pipeline — source first, no invented changes

This is a **compact execution guide** for the existing, authoritative
[commentary seven-stage workflow](COMMENTARY_7_STAGE_WORKFLOW.md), itself
based on the [Bible workflow](BIBLE_7_STAGE_WORKFLOW.md). It does **not**
create another sequence or override that document. The stages express
release gates, **not** an artificial deadline or a set of mandatory
one-off helper scripts. Each completed step has a source-bound,
independently reproducible receipt in its GitHub issue. A tool's status
is never a substitute for a source-specific editorial or rights decision.

| Official stage | Required evidence and reusable tooling |
| --- | --- |
| 1/7. **Select source and rights** | Work/edition and licensor; source rights for digital corrections, not just historic author. `commentary_intake.py --stage 1` is metadata-only research. |
| 2/7. **Pin originals** | Download observed compiled ZIP to a *private temporary directory*, independently record hash/size and declared driver/versification; review discrepancy, then require exact SHA at `--stage 2`. Never silently repin. |
| 3/7. **Original commentary audit** | Inventory all occupied native K/I/TOP slots, authorial headings, ranges, notes, citation links and markup using `commentary_native_inventory.py` / `commentary_native_raw_inventory.py`. Entry count is not section count. |
| 4/7. **SWORD integrity and source parity** | Select exact-stock reuse (strict compiled-source equality) or source-corrected rebuild (reversible attested deltas); verify full original/candidate native text, punctuation, notes, references, identity and links with `compiled_stock_commentary_proof.py` or `reviewed_compiled_commentary_rebuild.py`. |
| 5/7. **Editorial decisions** | Classify digital corruption vs intentional edition/author choice vs rendering defect; review source-bound patches and legal rights, preserve original text/divisions, and obtain explicit human approval. |
| 6/7. **Independent readers** | Run real `diatheke`, selected Xiphos and/or AndBible checks with explicit PASS/FAIL/NOT TESTED/INCONCLUSIVE outcomes; no claim that a CLI smoke confirms GUI layout. |
| 7/7. **Approve and publish** | Signed source/rights/reader decision; `validate.py`, `release_preflight.py`, `build.py`, `catalogue_release_coverage.py`, then **one** `pages.yml` Release-before-Pages workflow and independent `verify_public_catalogue.py` download/hashes. |

Each stage's reviewed input/output and next action belongs in its existing
GitHub import issue. Subchecks may run in batches without altering the
seven source-controlled completion gates. A completed stage is not another
publication permission, and a published source may still expose separate
application display bugs.


## Source-format and language neutrality — design constraint (2026-11-18)

**The import/reconstruction engine must not be built around English MHC, CCEL,
a particular commentary, or one book/verse scheme.** Research-only MHC
experiments under \`research/mhc-ccel/\` are historical feasibility evidence,
not a new production importer, accepted data model, or instruction to add
MHC-specific exceptions. The CCEL trial's SWORD CLI success is not a complete
source-structure or reader-parity proof.

The reusable design should extend existing tooling in this order:

1. **Source acquisition and source-native inventory:** keep exact original
   bytes, formats, encoding, language metadata, edition and rights provenance;
   use format-aware adapters for *actual* SWORD, OSIS, USFM or ThML sources.
   Do not translate, silently normalize Unicode/punctuation or assume English
   book names. Preserve original labels separately from canonical reference
   identifiers; use the source's own versification.
2. **Lossless structural inspection:** represent, in memory, ordered original
   text nodes, paragraphs, poetry, headings, quotes, notes, hyperlinks,
   introductions, section identities, original full ranges and source
   positions. The source markup remains authoritative, not a hand-invented
   proprietary replacement. Flag structures the chosen standards cannot
   express without loss rather than dropping them.
3. **Language-independent mapping and diagnostics:** preserve duplicate-start
   sections as distinct source identities; classify incompatible SWORD address
   ownership without selecting a winner, concatenating silently, or inventing
   first-verse aliases. Use exact text/markup and reference comparisons as
   baseline. Any optional linguistic tokenization must be language-aware,
   explicitly configured, advisory, and never a source mutation or release
   requirement (e.g. no English-only word regex or case heuristics).
4. **Standard output and reversible build:** choose a supported
   SWORD/OSIS/USFM conversion route appropriate to the *actual* source;
   retain evidence for unsupported mappings. Compile only after every
   independently inventoried source unit has an explicit preserved, mapped
   or blocked disposition. Audit the compiled SWORD native index, complete
   text, punctuation, headings, note/reference targets, structure, and
   introductions against the originals; record every transformation.
5. **Cross-language acceptance:** validate the same engine with at least one
   real English and one real French source, including accents, apostrophes,
   Unicode, names/references and source-specific versification; add other
   languages without branching the core by language. A passing English
   example alone is not a generic implementation certificate.

The existing seven-stage, per-edition rights/editorial/reader approval gates
remain unchanged. MHC is a demanding **fixture** for the reusable pipeline,
not an architectural dependency. A temporary incomplete MHC experiment must
not become an automatically required CI job for unrelated resource changes.

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
