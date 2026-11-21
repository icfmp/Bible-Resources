# Commentary research helpers

This package contains **read-only, non-CLI** evidence-gathering functions. They do not alter commentary content, infer an author's intended scope, or authorize a SWORD release. The source identity and native key are still checked by the invoking audit.

| Helper | What it examines |
| --- | --- |
| [`commentary_chapter_cross_slot.py`](commentary_chapter_cross_slot.py) | Alternate native slots for chapter-adjacent material |
| [`commentary_chapter_neighbors.py`](commentary_chapter_neighbors.py) | Neighboring chapter and verse structures |
| [`commentary_chapter_p_boundaries.py`](commentary_chapter_p_boundaries.py) | Paragraph boundaries and source scope anchors |
| [`commentary_chapter_paragraph_overlap.py`](commentary_chapter_paragraph_overlap.py) | Candidate overlapping paragraph spans |
| [`commentary_chapter_ref_labels.py`](commentary_chapter_ref_labels.py) | Original reference-label locations |
| [`commentary_editorial_topology.py`](commentary_editorial_topology.py) | Numeric native headings, occupied verse slots and shared raw bodies |
| [`commentary_intro_chapter_text_review.py`](commentary_intro_chapter_text_review.py) | Introduction text relative to numbered commentary entries |
| [`commentary_paragraph_witness_probe.py`](commentary_paragraph_witness_probe.py) | Paragraph anchors across independent digital witnesses |
| [`commentary_osis_rebuild_preflight.py`](commentary_osis_rebuild_preflight.py) | Whether original native frames can be wrapped as *test-only* OSIS without changing inner XML |
| [`commentary_lexical_overlap.py`](commentary_lexical_overlap.py) | Bounded source-versus-stock lexical overlap without exporting text |
| [`commentary_chapter_body_evidence.py`](commentary_chapter_body_evidence.py) | Chapter-unit boundaries, book identity and native coverage evidence |

Imported by the existing source-neutral section-scope audit and individually tested with invented fixtures. The lexical and chapter-body diagnostics were extracted from the CLI audit without changing their algorithms. Import via `research.commentary.<module>` with `scripts/` on `PYTHONPATH`. No root-level import shims, duplicate modules or executables are provided.

**Separate observations from decisions.** Similar-sounding helpers have different inputs, outputs and evidence limits. None is removable or interchangeable without a source-bound equivalence review. [Script maintenance #430](https://github.com/icfmp/Bible-Resources/issues/430) tracks this work; the [production contract](../../../docs/PRODUCTION_PIPELINE.md) remains authoritative.
