# Commentary research helpers

This package contains **read-only, non-CLI** evidence-gathering functions. They do not alter commentary content, infer an author's intended scope, or authorize a SWORD release. The source identity and native key are still checked by the invoking audit.

| Helper | What it examines |
| --- | --- |
| [`commentary_chapter_cross_slot.py`](commentary_chapter_cross_slot.py) | Alternate native slots for chapter-adjacent material |
| [`commentary_chapter_neighbors.py`](commentary_chapter_neighbors.py) | Neighboring chapter and verse structures |
| [`commentary_chapter_p_boundaries.py`](commentary_chapter_p_boundaries.py) | Paragraph boundaries and source scope anchors |
| [`commentary_chapter_paragraph_overlap.py`](commentary_chapter_paragraph_overlap.py) | Candidate overlapping paragraph spans |
| [`commentary_chapter_ref_labels.py`](commentary_chapter_ref_labels.py) | Original reference-label locations |
| [`commentary_nonlink_analysis.py`](commentary_nonlink_analysis.py) | Bounded plain-word accounting and separate Unicode word alignment, both unchanged |
| [`commentary_original_div1_book_consistency.py`](commentary_original_div1_book_consistency.py) | Original source div1 section/book-code contradictions for independent review |
| [`commentary_stock_prefix_topology.py`](commentary_stock_prefix_topology.py) | Native XML prefix topology compared with authenticated authored word sequences |
| [`commentary_shared_raw_source_units.py`](commentary_shared_raw_source_units.py) | Source-unit membership of shared native raw commentary runs |
| [`commentary_source_native_boundaries.py`](commentary_source_native_boundaries.py) | Original ThML/stock SWORD source-marker boundary evidence |
| [`commentary_navigation_link_plan.py`](commentary_navigation_link_plan.py) | Candidate source-scoped, versification-checked link plans, never automatic edits |
| [`commentary_reference_registry_triage.py`](commentary_reference_registry_triage.py) | Unambiguous original OSIS reference targets checked against authentic native verse registry |
| [`commentary_original_bookcode_repair.py`](commentary_original_bookcode_repair.py) | Reversible proposal for authorial book-code mismatches, never automatic edits |
| [`commentary_source_english_osis_alias.py`](commentary_source_english_osis_alias.py) | Pinned original div1 titles against canonical alias witnesses without inferring authorial scope |
| [`commentary_bookcode_repair_receipt_guard.py`](commentary_bookcode_repair_receipt_guard.py) | Fail-closed private authorial book-code repair receipt verification |
| [`commentary_osis_paragraph_presence.py`](commentary_osis_paragraph_presence.py) | Original CCEL/OSIS paragraph location comparison, not authorial parity |
| [`commentary_osis_transport_probe.py`](commentary_osis_transport_probe.py) | Private original numbered SWORD XML into OSIS transport and readback |
| [`commentary_xiphos_heading_probe.py`](commentary_xiphos_heading_probe.py) | Actual isolated Xiphos chapter-introduction and menu behavior evidence |
| [`commentary_unresolved_lexical_triage.py`](commentary_unresolved_lexical_triage.py) | Bounded word-level mismatches and source-joined mark positions, without text export |
| [`commentary_near_prose_unicode_review.py`](commentary_near_prose_unicode_review.py) | Separate original/stock Unicode normalization witnesses, never a rewrite |
| [`commentary_source_identity_lexical_gate.py`](commentary_source_identity_lexical_gate.py) | Quarantine contradictory original title/book-code joins before lexical comparisons |
| [`commentary_prose_cross_slot.py`](commentary_prose_cross_slot.py) | Alternative native slot evidence for original commentary prose without inferred placement |
| [`commentary_reference_cross_slot.py`](commentary_reference_cross_slot.py) | Original/native Scripture target and XML link topology across slots |
| [`commentary_link_disposition_review.py`](commentary_link_disposition_review.py) | Source-pinned MHCC Modern link-correction proposal checks against original link hashes; no edits or release approval |
| [`commentary_original_link_identity.py`](commentary_original_link_identity.py) | Byte-pinned native original link identities, targets and link-label hashes; no text export or publication |

Each helper has its own documented script and test consumers; not every helper is imported by the section-scope audit. The surviving lexical diagnostics, original link identities and modern proposal-review gate were extracted without changing their algorithms. The latter remains tied to the attested MHCC Modern manuscript and source edition; it is not a generic editorial rule. The former two unlinked-word root helpers are now grouped into one import-only research module; all eight original functions remain distinct and verbatim. Import via `research.commentary.<module>` with `scripts/` on `PYTHONPATH`. No root-level import shims, duplicate modules or executables are provided. Five further non-CLI lexical, source-identity and cross-slot observers now live in this same package; their function bodies and input/output contracts were not changed, and real importer/test paths were updated.

Original native-link identity checks remain private observations: an authenticated destination or label digest is not evidence that a translated manuscript preserves the reference. The parent runner remains responsible for source-pinned native streaming and editorial/release gatekeeping.

The unified nonlink library deliberately keeps different bounds for each calculation: large-input accounting must never be mistaken for bounded longest-common-subsequence alignment. Existing tests continue to verify these differences.

**Canonical-title witness:** `commentary_source_english_osis_alias.py` reads the checked-in 66-book OSIS/USFM crosswalk from the repository root, not from this research package. The module-relative root lookup was updated on relocation, and its existing direct tests still load and verify the complete real 66-book registry. Neither a matching English title nor a normalized word is authorization to change an original `scripCom` marker, reference or exposition.

## Verify the package without exposing source content

From the repository root, run the direct synthetic regressions and then the
full production validation; the library files themselves have no CLI:

```sh
python -m unittest discover -s tests -p 'test_commentary_reference_cross_slot.py' -v
python -m unittest discover -s tests -p 'test_commentary_source_identity_lexical_gate.py' -v
python -m unittest discover -s tests -p 'test_commentary_unresolved_lexical_triage.py' -v
python scripts/tool_registry.py --check
```

A passing lexical or native-slot helper test does not independently attest an
external author's changed source archive. Preserve source SHA pins and run the
separate source/native reader acceptance gate before any editorial decision.

**Separate observations from decisions.** Similar-sounding helpers have different inputs, outputs and evidence limits. None is removable or interchangeable without a source-bound equivalence review. [Script maintenance #430](https://github.com/icfmp/Bible-Resources/issues/430) tracks this work; the [production contract](../../../docs/PRODUCTION_PIPELINE.md) remains authoritative.
