# Bible source/native research libraries

These modules are **import-only**, read-only evidence utilities shared by
Bible edition workflows. They are not importers, compilers, release tools or
authority to modify an original translation. The real production commands
remain in `scripts/` and use these exact checked helpers.

| Helper | Verified responsibility |
| --- | --- |
| [`source_usfx_structure.py`](source_usfx_structure.py) | Preserve and classify the authored USFX book/chapter/verse and layout inventory |
| [`private_sword_install.py`](private_sword_install.py) | Safety-check and isolate one original stock SWORD Bible ZIP for generic read-only QA |
| [`native_absorbed_verse_groups.py`](native_absorbed_verse_groups.py) | Check if source-only verse words survive in a neighboring native slot, without approving a merge |
| [`source_native_nonspace_boundaries.py`](source_native_nonspace_boundaries.py) | Compare source/native punctuation-relative paragraph and poetry boundaries without rewriting words |
| [`source_native_structure_topology.py`](source_native_structure_topology.py) | Compare structural open/close anchors while preserving authored scope and order |
| [`source_native_osis_target_addressability.py`](source_native_osis_target_addressability.py) | Check authored OSIS reference targets against actual native SWORD keys without creating verses |
| [`source_native_osis_boundary_positions.py`](source_native_osis_boundary_positions.py) | Compare OSIS-authored and native SWORD book/verse structural boundaries without exporting source text |
| [`source_native_osis_structure_screen.py`](source_native_osis_structure_screen.py) | Read-only OSIS to native markup structure census with text excluded from reports |
| [`source_native_scope.py`](source_native_scope.py) | Compare independently attested verse-key scope with the native SWORD keys |
| [`source_native_notes_audit.py`](source_native_notes_audit.py) | Source/native numbered and non-numbered note identity and completeness evidence |
| [`source_native_paragraph_counts.py`](source_native_paragraph_counts.py) | Source paragraph and poetry structure vs installed native entry signatures |
| [`source_native_note_positions.py`](source_native_note_positions.py) | Exact authored note-caller positions vs raw native SWORD structures |
| [`source_native_layout_anchors.py`](source_native_layout_anchors.py) | Source/native paragraph, poetry and heading anchor comparisons |
| [`native_milestone_pair_audit.py`](native_milestone_pair_audit.py) | Strict compiled SWORD verse milestone sID/eID pairing without inserting a verse |
| [`native_sword_markup_census.py`](native_sword_markup_census.py) | Metadata-only original native XML markup census |
| [`note_whitespace_diagnostics.py`](note_whitespace_diagnostics.py) | Read-only note whitespace difference categories, preserving literal source |
| [`maintext_whitespace_patterns.py`](maintext_whitespace_patterns.py) | Source/native main-text whitespace topology, not editorial normalization |
| [`source_native_ordered_body.py`](source_native_ordered_body.py) | Original authored opening-event order against native entry shapes |
| [`source_native_word_boundaries.py`](source_native_word_boundaries.py) | Source vs native paragraph/poetry boundary word anchor evidence |

Do not infer a missing verse, new reference destination or a source error
from a SWORD reader's available address space. Mark source-only, unaddressable
and ambiguous records as such. Preserve literal Scripture, punctuation, note
contents, authorial layout and versification, including apparently unusual
original edition choices.

The real USFX-schema and compiled-SWORD validators, canonical
[production workflow](../../../docs/PRODUCTION_PIPELINE.md), and
edition-specific evidence remain separate. The [script registry](../../../reports/tooling/TOOL_REGISTRY.md)
lists consumers and tests but does **not** certify upstream source identity.
The following direct regressions exercise the helpers without publishing
source words:

```sh
python -m unittest discover -s tests -p 'test_private_sword_install.py' -v
python -m unittest discover -s tests -p 'test_source_usfx_structure.py' -v
python -m unittest discover -s tests -p 'test_source_native_notes_audit.py' -v
python scripts/tool_registry.py --check
```
