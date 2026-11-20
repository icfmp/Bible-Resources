# Source-to-native note comparison

**Purpose:** compare authored USFX notes associated with numbered verses against the corresponding native SWORD entries **without exporting publisher text**. This is a read-only diagnostic, not an editorial approval.

## Source and native evidence

`scripts/source_native_notes_audit.py` inventories source note markers `f`, `fe`, `x`, `ef`, `ex` and `note`. It identifies notes inside mapped numbered verses, separately counts notes outside those verses, and flags ambiguous verse/note nesting. Its companion `scripts/source_native_maintext_probe.py` inspects actual compiled `RawText` or `zText` entries in an isolated SWORD installation.

Record the exact source edition, archives, SHA-256, native driver and versification, and the independently reviewed book crosswalk before comparing. Source-only verses, additional books and unaddressable native entries must remain explicit.

## Classifications to retain

- Equal source/native counts of notes per numbered key, or count mismatches.
- Equal ordered note bodies, NFC/whitespace differences, or genuinely different bodies.
- Native XML fragments that cannot be parsed safely: **unknown**, never interpreted as empty notes.
- Authored source notes without an independently addressable native key.
- Source note type and OSIS `note type`, literal callers against `n` (excluding automatic `+`/`-` markers), and explicit source `ref[@tgt]` versus native `reference[@osisRef]` attributes.
- An absent explicit destination is **not** a license to invent one from text such as `xt` or `xo`. Native `reference type="annotateRef"` indicates an annotation source, not a destination link.

Only compare note positions or identities when the actual source/native mapping supports them. A count mismatch forbids arbitrary positional pairing.

## Security and limitations

All original note bodies, callers, and target strings remain private. Reports may include bounded reference identifiers, counts, classifications and trusted hashes, **never copied note prose**.

Even matching note bodies cannot establish caller/anchor location, styles, note type, exact cross-reference resolution, nested markup, paragraph/poetry preservation or source-to-native text fidelity. Malformed native snippets remain unresolved. Independently execute the relevant [production stages](../PRODUCTION_PIPELINE.md) and [main text audit](SOURCE_NATIVE_MAIN_TEXT.md).

For the tool's actual inputs and run context, refer to `scripts/source_native_maintext_probe.py` and its tests. Store dated per-edition results in `sources/cleaned/**/editorial/evidence/`, not this reusable procedure.
