# LSG source-to-SWORD research handoff (historical PR #24)

The exhaustive first-Louis-Segond source build and diagnostic experiments are preserved in [PR #24](https://github.com/icfmp/Bible-Resources/pull/24) at commit `7f675b4d621e5c0aba5fd78f0cb3cb468eb2cd26`, **on top of** the older [PR #18](https://github.com/icfmp/Bible-Resources/pull/18). Do not merge these old experimental branches wholesale into the currently published pipeline. Their original experiments have already informed the first [released LSG 0.1.0](releases/LSG-0.1.0.md), whose immutable file hashes, owner-approved source→SWORD index compromise, release audit, original source archives, and technical caveats are recorded separately in `main`.

## Independently reusable pieces recovered

- `scripts/private_sword_bundle.py` and `tests/test_private_sword_bundle.py` — a bounded, deterministic **private-only** SWORD ZIP and isolated reinstallation proof, with source-byte fingerprints, actual stock `diatheke` comparison and explicit edition-specific representative passages. No hardcoded LSG samples. This is not an automatic release or source-text fidelity approval; `output_archive` deliberately creates a test-only ZIP and must not be used for publication without separate authorization.
- `scripts/note_whitespace_diagnostics.py` and `tests/test_note_whitespace_diagnostics.py` — privacy-safe, source-text-free categorical note whitespace diagnostics. Normalized word-token equality does not authorize discarding original line breaks or typography.

Both tools are **ingredients** for a generic validation process, not an integrated automatic SWORD source-to-compiled exhaustive corpus comparator. The already merged [#33](https://github.com/icfmp/Bible-Resources/pull/33) requires verse-index proof for approved Bibles and [#35](https://github.com/icfmp/Bible-Resources/pull/35) recovers bounded reader filter options.

## Research code retained only on historical branch

| Audit group | Historical files | Generic migration still required |
| --- | --- | --- |
| Real eBible source → Segond stock SWORD | `scripts/lsg_stable_source_trial.py`, `scripts/lsg_sword_rebuild.py`, `config/lsg-reviewed-verse-merges.json` | Decouple edition, source archive names, converter revision, authorial key count and fixed index exception; independently audit source/reader key producer |
| Entire compiled markup and intros | `scripts/lsg_stock_raw_markup.py`, `scripts/lsg_stock_layout_markers.py`, C++ `sword_raw_markup_*.cpp` | Resolve stock SWORD data generically, include ordinary and verse-zero keys, and test another module |
| Original ordered Strong/lemma values | `scripts/lsg_stock_lemma_parity.py`, `scripts/sword_raw_lemma_values.cpp` | Check exact source ordinals, value and independent rights; support editions without lemmas |
| Notes: bodies/callers/anchors | `scripts/lsg_stock_note_text.py`, `scripts/lsg_stock_note_anchors.py`, `scripts/lsg_stock_publisher_note_parity.py`, C++ note inspectors | Original-authorial USFX versus compiled text, caller/type, whole-book ordinal anchors and punctuation/spacing fidelity, without hardcoded source count |
| Layout and cross-reference provenance | `scripts/lsg_stock_layout_boundaries.py`, `scripts/lsg_stock_reference_parity.py`, `scripts/osis_text_only_parallels.py` | Preserve all original authorial start/end positions and source explicit targets; never confuse SWORD-generated `refList` suggestions with authorial links |
| Release acceptance | `scripts/lsg_xiphos_preview.py`, `docs/LSG_XIPHOS_ACCEPTANCE_PLAN.md` | Actual Xiphos and another independent consumer; separately record technical/visual editorial approval |

The source-bound review of Mark 10:52–53 **is already committed to `main`** as `modules/lsg-1910/SOURCE_REFERENCE_MERGES.json`, attested against the originally released full source audit and immutable package. No duplicate LSG-only validator is needed merely to preserve that evidence.

## What the historical reports proved — and did not prove

The retained real-run evidence reports 31,170 source-authored verse keys, 31,169 accessible ordinary SWORD entries (including the one explicitly reviewed adjacent merge), plus 1,255 verse-zero introduction entries, 705,728 ordered lemma-bearing words, 9,751 notes, 22,490 reference tags, and correctly paired 11,436 structural openings and closings. Original-USFX note word/punctuation parity was separately shown under normalization; original note typography was **not** byte-identical. These are historical **source-specific** findings, not claims that the new standalone generic helpers reproduce all these audits themselves.

Live reader and content renderings are separate. Xiphos GUI rendering was not certified. The published edition intentionally documents its Mark 10:52–53 index compromise, Job 34:37 source absence, targetless heading references and intro formatting residue. Do not rewrite any Bible source or fill an absent verse to "fix" a research report.

## Next test required before claiming full generic automation

Follow [issue #28](https://github.com/icfmp/Bible-Resources/issues/28): build a documented end-to-end, source-independent inventory producer; exercise **a second real cleared Bible** with a different structure and, where appropriate, different SWORD driver; verify full original text, notes, links, word anchors and structure against that edition without adding test-specific exceptions. Reproduce the existing immutable release evidence without changing its published bytes.

The archived PR branch is a reproducibility and research reference, **not** an open-ended production release PR. Preserve branch commits and evidence links; no source publication or update is authorized by this handoff.
