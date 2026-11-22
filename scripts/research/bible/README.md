# Bible source/native research libraries

These modules are **import-only**, read-only evidence utilities shared by
Bible edition workflows. They are not importers, compilers, release tools or
authority to modify an original translation. The real production commands
remain in `scripts/` and use these exact checked helpers.

| Helper | Verified responsibility |
| --- | --- |
| [`source_usfx_structure.py`](source_usfx_structure.py) | Preserve and classify the authored USFX book/chapter/verse and layout inventory |
| [`source_native_scope.py`](source_native_scope.py) | Compare independently attested verse-key scope with the native SWORD keys |
| [`source_native_notes_audit.py`](source_native_notes_audit.py) | Source/native numbered and non-numbered note identity and completeness evidence |
| [`source_native_paragraph_counts.py`](source_native_paragraph_counts.py) | Source paragraph and poetry structure vs installed native entry signatures |
| [`source_native_note_positions.py`](source_native_note_positions.py) | Exact authored note-caller positions vs raw native SWORD structures |
| [`source_native_layout_anchors.py`](source_native_layout_anchors.py) | Source/native paragraph, poetry and heading anchor comparisons |

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
python -m unittest discover -s tests -p 'test_source_usfx_structure.py' -v
python -m unittest discover -s tests -p 'test_source_native_notes_audit.py' -v
python scripts/tool_registry.py --check
```
