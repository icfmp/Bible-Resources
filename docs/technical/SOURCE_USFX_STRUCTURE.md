# Original USFX structural inventory

**Purpose:** inspect every book, chapter, verse and structural marker of a publisher's original USFX source **without altering it**. USFX is an input format, not itself proof of the canonical OSIS output or permission to redistribute text.

## Verification procedure

1. Identify and pin the exact source archive, publisher edition/revision, licence, URL and SHA-256.
2. Independently validate the original against the reviewed, SHA-pinned USFX schema described in `config/usfx-schema-policy.json`. An XML parse alone is insufficient.
3. Run the read-only `audit_source_usfx(xml: bytes)` function in `scripts/source_usfx_structure.py`. **This module has no standalone CLI**. The following example uses a private original XML file, emits only text-free metadata, and does not claim to validate its official XSD:
4. Review counts and order of **all** authored books, chapter markers and numbered verses. Record native source-only books or unusual versification explicitly.
5. Inspect original XML element/attribute occurrence counts; ordered structural hashes; paragraph/poetry/heading markers; note kinds and callers; and explicitly encoded reference destinations.
6. Classify duplicates, reversed or inconsistent ranges, ambiguous nesting, unknown elements and nonstandard constructs as **BLOCKED**, not automatically corrected.

Example, after independently validating the exact original USFX against the pinned official schema:

```sh
PYTHONPATH=scripts python - <<'PY'
import json
from pathlib import Path
from source_usfx_structure import audit_source_usfx

original = Path("/private/source.usfx.xml")
report = audit_source_usfx(original.read_bytes())
Path("/private/source-usfx-inventory.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
print(report["status"], report["source_book_count"])
PY
```

The emitted receipt must contain metadata, structural digests and bounded reference IDs, not original Scripture, note content, title text or private reference target strings. The function explicitly reports `official_usfx_schema_validated: false` because XSD validation is a **separate step**; do not promote the inventory result into a schema approval.

## Source-only and compilation boundaries

- Source labels, verse endings, speaker styles, notes outside numbered text and source-only books remain part of the author's edition; do not silently strip them or treat every marker as Scripture prose.
- A source can pass USFX structure checks while still having errors in OSIS conversion, native SWORD verse indexing, text/notes/links, reader display or rights.
- When redistributing an approved stock module without converting source USFX, record **conversion not performed**; do not invent an OSIS master or claim source/native equivalence without independent proof.
- A rebuilt edition requires its own full original-to-cleaned and cleaned-to-native comparison, with source-attested decisions for every difference.

For executable staging use [Bible onboarding](../workflows/BIBLE_7_STAGE_WORKFLOW.md), [stage automation](../workflows/BIBLE_STAGE_AUTOMATION.md), [OSIS source inventory](SOURCE_OSIS_INVENTORY.md) and the [production contract](../PRODUCTION_PIPELINE.md). Keep real-edition run IDs, anomalies and editorial decisions beside the edition in `sources/cleaned/**/editorial/evidence/`.
