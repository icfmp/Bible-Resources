# Bible source/native research libraries

These modules are **import-only**, read-only evidence utilities shared by
Bible edition workflows. They are not importers, compilers, release tools or
authority to modify an original translation. The real production commands
remain in `scripts/` and use these exact checked helpers.

| Helper | Verified responsibility |
| --- | --- |
| [`source_usfx_structure.py`](source_usfx_structure.py) | Legacy original-USFX structure inventory, temporarily used only by the ordered-body helper |
| [`private_sword_install.py`](private_sword_install.py) | Safety-check and isolate one original stock SWORD Bible ZIP for generic read-only QA |
| [`source_native_osis_target_addressability.py`](source_native_osis_target_addressability.py) | Check authored OSIS reference targets against actual native SWORD keys without creating verses |
| [`source_native_osis_boundary_positions.py`](source_native_osis_boundary_positions.py) | Compare OSIS-authored and native SWORD book/verse structural boundaries without exporting source text |
| [`source_native_osis_structure_screen.py`](source_native_osis_structure_screen.py) | Read-only OSIS to native markup structure census with text excluded from reports |
| [`source_native_paragraph_counts.py`](source_native_paragraph_counts.py) | Original USFX paragraph metadata helper still needed by ordered-body comparisons; targeted for removal after source-format decoupling |
| [`source_native_note_positions.py`](source_native_note_positions.py) | Exact authored note-caller positions vs raw native SWORD structures |
| [`native_milestone_pair_audit.py`](native_milestone_pair_audit.py) | Strict compiled SWORD verse milestone sID/eID pairing without inserting a verse |
| [`native_raw_main_text.py`](native_raw_main_text.py) | Source-format-independent strict native SWORD main-text parsing, excluding note/title bodies and rejecting invalid XML |
| [`source_osis_verse_notes.py`](source_osis_verse_notes.py) | Strict original OSIS numbered-verse text, note caller, note body and anchor evidence used privately by OSIS source/native validators; never publish returned source text |
| [`native_sword_markup_census.py`](native_sword_markup_census.py) | Metadata-only original native XML markup census |
| [`source_native_ordered_body.py`](source_native_ordered_body.py) | Shared OSIS/SWORD ordered-body comparison; historical USFX parsing retained only until this helper is split |

Do not infer a missing verse, new reference destination or a source error
from a SWORD reader's available address space. Mark source-only, unaddressable
and ambiguous records as such. Preserve literal Scripture, punctuation, note
contents, authorial layout and versification, including apparently unusual
original edition choices.

The source-OSIS, native SWORD and compiled-text validators, canonical
[production workflow](../../../docs/PRODUCTION_PIPELINE.md), and
edition-specific evidence remain separate. The [script registry](../../../reports/tooling/TOOL_REGISTRY.md)
lists consumers and tests but does **not** certify upstream source identity.
The following direct regressions exercise the helpers without publishing
source words:

```sh
python -m unittest discover -s tests -p 'test_private_sword_install.py' -v
python -m unittest discover -s tests -p 'test_source_usfx_structure.py' -v
python -m unittest discover -s tests -p 'test_source_osis_verse_notes.py' -v
python scripts/tool_registry.py --check
```
