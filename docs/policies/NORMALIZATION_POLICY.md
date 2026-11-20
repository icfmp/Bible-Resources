# Source normalization policy (OSIS-first)

Normalize only the **technical representation** of source-attested structure. The identified edition's words, punctuation, readings, note bodies/anchors, verse mapping, commentary scopes, poetry, paragraphs and editorial meaning are not cosmetic noise.

The [BRNP proposal](../architecture/BRNP.md) records a future shared target profile; implementation and enforcement are deferred to [issue #451](https://github.com/icfmp/Bible-Resources/issues/451). **Do not interpret it as an approved release gate today.**

## Standards and accepted representations

Official [CrossWire OSIS Bible](https://wiki.crosswire.org/OSIS_Bibles), [OSIS/TEI validation](https://wiki.crosswire.org/Validate_OSIS_or_TEI_text) and [SWORD module configuration](https://wiki.crosswire.org/DevTools:conf_Files) are authoritative. The locally pinned official OSIS 2.1.1 XSD is mandatory for OSIS Bibles and commentaries. The reviewed `config/osis-policy.json` subset is **additional project policy**, not a replacement XML schema. TEI dictionaries, USFM/USFX and compiled SWORD require their own format-specific, independently tested source adapters.

Original data must be stored unchanged and source/edition/rights/SHA-256 pinned. A compiled `zText`, `zCom` or other SWORD module is not original authoring XML. If only compiled data are available, diagnostics identify provider/module/native key; never invent original XML file and line numbers.

## Invariants

- Keep every authored word, punctuation mark, translation decision, attribution, canonical gap, versification and note/reference association.
- Preserve genuine `p`, `lg`, `l`/`level`, `title`, `q`, `hi`, `transChange`, `divineName`, `note`, `reference` and `w`/lexical alignment relationships and overlapping milestones.
- Do not guess missing verses, paragraph boundaries, chapter commentary scope, reference targets, case, italicization or authorial quotations.
- A mapping to a different but equivalent standards-valid representation requires a **reviewed, source-attested, reversible rule** with independent golden positive/negative fixtures. Unknown but OSIS-valid elements or unreviewed variants stop processing with precise location; do not flatten or discard them.
- A different printed/digital edition can serve as evidence for an **explicitly separately identified editorial adaptation**, subject to rights and review. It does not silently redefine the identified source edition's own layout.
- A schema-valid XML tree is not a guarantee of source-to-native SWORD text, note, reference, structure or reader parity.

## Available tools

The project pins the CrossWire XSD and its W3C XML dependency in [`config/osis-policy.json`](../../config/osis-policy.json), including approved SHA-256 values and import policy. Do not automatically repin changed upstream bytes.

```sh
python scripts/fetch_reviewed_schema.py --directory /tmp/reviewed-osis
python scripts/guard_osis.py /private/original.osis.xml \
  --schema /tmp/reviewed-osis/osisCore.2.1.1-cw-latest.xsd \
  --report /private/source-validation.json
```

The read-only `scripts/guard_osis.py` checks the exact original XML, official XSD, reviewed elements, poetry and milestones; it does **not** normalize. `scripts/guard_commentary.py` adds commentary passage semantics, not a second XML dialect. `scripts/audit_osis.py` is read-only; `scripts/normalize_osis.py` applies only **explicitly approved source-hash-bound transformations** to a different output path (reviewed paragraph splits, child-boundary splits, poetry grouping). See the [editorial audit procedure](../workflows/EDITORIAL_AUDIT_WORKFLOW.md).

## Decision and failure procedure

For any novel construct: preserve a source-pinned diagnostic; classify as invalid XML, official-OSIS-valid but not yet supported, or another input format; consult the standard; approve a minimal mapping, rights and source/target comparison; add synthetic regressions; rerun the whole resource. Never expand a permissive parser fallback merely to quiet a failure.

A valid `SOURCE_VALIDATION.json` records source/schema/policy checksums and status but does **not** attest unpublished publisher bytes or approve a public release. Publication additionally requires full original-to-cleaned/native parity, correct module metadata, rights, independent readers and owner sign-off, under the [production contract](../PRODUCTION_PIPELINE.md).
