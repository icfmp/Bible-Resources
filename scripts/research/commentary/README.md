# Commentary chapter research modules

These five modules are **non-CLI, source-bound research helpers** previously scattered across the top-level `scripts/` directory. Grouped here to make chapter/section topology investigations discoverable without mistaking them for general release or editorial approval procedures.

| Module | Research responsibility |
| --- | --- |
| [`commentary_chapter_cross_slot.py`](commentary_chapter_cross_slot.py) | Alternative native-record locations for chapter-scoped content |
| [`commentary_chapter_neighbors.py`](commentary_chapter_neighbors.py) | Neighboring chapter/verse structures and comparison |
| [`commentary_chapter_p_boundaries.py`](commentary_chapter_p_boundaries.py) | Paragraph boundary and source scope anchors |
| [`commentary_chapter_paragraph_overlap.py`](commentary_chapter_paragraph_overlap.py) | Paragraph overlap topology |
| [`commentary_chapter_ref_labels.py`](commentary_chapter_ref_labels.py) | Cross-reference label location |

Callers now use `from research.commentary.commentary_chapter_neighbors import …` and related package-qualified imports, with the existing `scripts/` root on the Python import path. No redundant compatibility shims or executable entrypoints were added. The generic script registry is tested to recognize qualified imports; its output remains an *inventory of candidates*, not proof of program execution.

This move **does not merge their algorithms**: semantically distinct full-corpus research outputs must be compared and proven equivalent before deleting or merging functions, tracked in [maintenance issue #430](https://github.com/icfmp/Bible-Resources/issues/430). For new Bible/commentary production follow the [source-first production contract](../../../docs/PRODUCTION_PIPELINE.md) and authorial scope rules.
