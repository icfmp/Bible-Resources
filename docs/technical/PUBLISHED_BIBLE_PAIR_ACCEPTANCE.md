# Published Bible pair: source, native and reader acceptance

Issue [#28](https://github.com/icfmp/Bible-Resources/issues/28). This is a bounded evidence reconciliation, not a new editorial or release decision.

## Exact identities

| Edition | SWORD module | Native system | Release ZIP SHA-256 |
| --- | --- | --- | --- |
| Louis Segond 1910 curated edition 1.0.4 | BRLSG1910 | Segond | `643b33b6f8130c46ec381394169c4ff3b60575b8e7d999ba550fbaeb36f65d05` |
| J. N. Darby 2024 curated edition 1.0.0 | BRJND2024 | Luther | `81acdfdfbbb18135a49609c045b293ce495a200b37f667f55c190925544b9553` |

Both releases use zText. No third Bible is required for this issue's owner-selected pair. No provider package, original source, published module or application was changed for the acceptance run.

## Stage evidence

| Stage | Evidence and result | Boundary |
| --- | --- | --- |
| Source identity and rights | Edition-local provenance and release authorization; original OSIS Darby and USFM/USFX Segond | No new edition rights inferred |
| Original-to-cleaned content | #569–#582; [original source gates](../workflows/BIBLE_7_STAGE_WORKFLOW.md), exact approved repair ledgers, independent USFM and USFX witnesses | Supported structural grammar, not a claim of every possible OSIS/USFM construct or exact typography |
| Reusable conversion | [#584](https://github.com/icfmp/Bible-Resources/pull/584), [final real-source run](https://github.com/icfmp/Bible-Resources/actions/runs/45653407810): repeat byte identity of raw and projected candidate, original source checks, zero pinned XSD errors | Private candidate, not approval; authored destination semantics and review remain separate |
| Native fidelity | [#576](https://github.com/icfmp/Bible-Resources/pull/576), [final Validate](https://github.com/icfmp/Bible-Resources/actions/runs/45653407695): actual stock SWORD readback for both approved modules; 572 tests | Original authored source keys and occupied native slots are distinct; edition-specific approved exceptions retained |
| Independent JSword | [two-edition engine audit](https://github.com/icfmp/Bible-Resources/actions/runs/45566303467), [LSG final candidate readback](https://github.com/icfmp/Bible-Resources/actions/runs/45575067478) | Engine readback, not current Android GUI approval |
| Xiphos | [historical source-layout GUI stage](https://github.com/icfmp/Bible-Resources/actions/runs/45569845095) succeeded in a run whose later JSword stage failed; Darby [historical reader QA](../../sources/cleaned/bibles/fr/darby-jnd-2024/editorial/evidence/darby-2024-0.1.1-final-reader-qa.md) | [Exact published pair run](https://github.com/icfmp/Bible-Resources/actions/runs/45661201362): standalone 2/2, parallel 3/6; mixed-numbering limitation documented below |
| Actual GTK Bible parallel | [successful run](https://github.com/icfmp/Bible-Resources/actions/runs/45660060897), research commit `018ccd5ea5c756b64e4f02597d43d297b82e19d4`, pinned app `3d794a2bba48c30022b64bb4faabc8be9a10f1e8` | Actual native host GTK; not a packaged Flatpak/Android test |
| Public distribution | [live catalogue and package checks](https://github.com/icfmp/Bible-Resources/actions/runs/45603375636) | Existing release only; no new release approved |

## Actual parallel reader result

The ordinary Bible Resources catalogue installation used exactly the two independently downloaded public ZIPs. All seven payload members of each installed module matched the corresponding archive byte-for-byte. Both directions passed all nine reference probes (18 native and 18 GTK cases), including Genesis 1, John 3, Psalms 3, Acts 19 and Ecclesiastes 11/12. In particular, Segond Eccl 12:1–2 correspond to Luther Eccl 11:9–10; Segond Eccl 12:3 corresponds to Luther Eccl 12:1. The two native-wheel sequences in John 3 passed in both pane orders without changing navigation history.

The initial two GTK assertions were not Scripture loss or bad versification. At Darby Ps 3:1, source-verified OSIS emphasis accounts for two generated SWORD plain-filter stars and associated spaces. The successful verifier proves both the native decorations' source boundaries and the matching document decoration ranges before excluding these generated stars from copied prose. It does not discard arbitrary literal asterisks, words or punctuation. Whitespace folding is explicit; this does not certify pixel-level typography.

The complete metadata-only result is retained in [the receipt](published-bible-pair-acceptance.json). The reader test lives in the retained research commit, not in an approved release workflow. Independent current Xiphos GUI observations are recorded below; full current Android GUI coverage is not established. Scope limits and genuine reader-only defects must be reported separately rather than fixed by changing the biblical resource.

## Independent released-reader observations

Actual Xiphos 4.2.1 (Ubuntu package `4.2.1+dfsg1-8build3`), [run 45661201362](https://github.com/icfmp/Bible-Resources/actions/runs/45661201362), research head `d7639b49b7ab7400e6f79004a021a79317b502d8`: all six diatheke native prose witnesses, both standalone GUI witnesses, and three of six exact same-row parallel prose witnesses passed. Two failed parallel probes contained both expected passages in different HTML rows (Eccl 12:3 Segond / 12:1 Luther, both directions); one did not establish both prose witnesses (Segond 12:1 / Luther 11:9). John 3:16 passed in both directions. Every installed module member remained byte-identical. The job deliberately reported failure rather than treating the unmatched rows as a pass.

The tagged [Xiphos 4.2.1 parallel renderer](https://github.com/crosswire/xiphos/blob/4.2.1/src/main/parallel_view.cc) (Git blob `12ccacd6dee1d62b867e874ebcd89c35aba92f76`) explicitly selects the first module's versification to generate a common key, then calls `set_module_key(mod, tmpkey)` and `get_render_text(mod, tmpkey)` for each column. Its own comment warns that this can be wrong for other modules. This explains why separately correct native entries can be displayed on the wrong comparison row. The evidence supports a third-party mixed-versification rendering limitation, not a source or native-index defect; the single unconfirmed witness remains inconclusive, not a missing verse. Do not change a correct resource's versification to compensate. No upstream correction or new edition is required by the owner-selected project scope.

The [Xiphos and diatheke metadata-only receipt](published-bible-xiphos-acceptance.json) preserves both passes and failures.

## Remaining acceptance boundaries

The owner requested only LSG and Darby, and does not require fixing external providers. Historical upstream comparisons and known issues are preserved in the edition evidence. Do not silently expand the comparison to a third edition, or assert new reader GUI coverage from engine-only evidence. The source/compiled gates and real GTK comparison results are verified; Xiphos's documented mixed-versification limitation remains a reader finding, not successful parallel acceptance. Current Android GUI coverage and unverified editorial structural or reference scopes must remain explicit; engine evidence is not GUI evidence. No claim of unrestricted reader interoperability is made.
