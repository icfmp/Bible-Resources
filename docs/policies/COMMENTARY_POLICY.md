# Commentary source policy

Commentaries obey the same source-identity, rights, official-XSD and fail-closed fidelity rules as Bibles, but **annotated passage scope** is not the same as numbered Scripture text. Use official [CrossWire OSIS commentary conventions](https://wiki.crosswire.org/OSIS_Commentaries), not a custom XML dialect.

## Entry structure and scope

An OSIS commentary entry is a `div` with `annotateType="commentary"` and an authorial `annotateRef` identifying a Bible verse, passage, chapter or reviewed discontinuous set. A `div type` value can describe section hierarchy but does **not** identify commentary coverage; headings, book wrappers and introductions are not implicitly assigned to a verse.

```xml
<div type="section" annotateType="commentary" annotateRef="Gen.1.1">
  <title>Authorial section heading</title>
  <p>Illustrative original commentary content.</p>
</div>
```

This fragment illustrates the mapping only; a real source must pass the official OSIS XSD. Preserve exact original annotation range bounds, order, nested sections, quotations, titles, lists, notes, references, paragraphs and typography. Do not merge two authorial comments just because they address the same passage, or split a chapter-only comment into invented verse comments.

The current `scripts/guard_commentary.py` implements an intentionally narrow reviewed subset of ordinary book/chapter/verse identifiers, ranges and lists. Unusual, otherwise legal references, cross-book ranges, introduction keys or ambiguous work prefixes **block for standards review**, rather than being silently simplified.

## Editorial corrections versus formatting

The authorial prose, theological argument, Scripture quotations and original sectioning are content. Do not remove quotations as duplicate Bible text or automatically re-paragraph for readability. A demonstrable wording, citation or annotation defect can be corrected only with attested evidence, reversible recorded change and appropriate approval. A separately identified modernized/translated derivative may follow a different reviewed editorial layout; it must not masquerade as the unchanged original.

## Reader discovery across a passage

Where independent evidence proves an entry covers a full chapter or passage but native SWORD indexes only its first key, a **separate explicitly reviewed corrected edition** may add navigational aliases so users can discover that single authorial entry at its actual covered verses. Do **not** copy the prose into independently authored per-verse entries, assume scope from a first-key shortcut, or overwrite distinct occupied keys.

Each alias must be derived from verified source scope and actual source/reader versification, with original and candidate byte hashes, complete link/topology comparison, deduplicated reader behavior and a reversible change receipt. The generic read-only proposal tool is `scripts/research/commentary/commentary_navigation_link_plan.py`. Any individual edition's decisions live in its `sources/cleaned/**/editorial/` folder.

## Validation and limits

First validate the exact source against the pinned OSIS 2.1.1 schema and generic guard. Then:

```sh
python scripts/guard_commentary.py /private/commentary.osis.xml \
  --schema /private/approved/osisCore.2.1.1-cw-latest.xsd \
  --report /private/commentary-validation.json
```

The report must bind the original SHA, pinned schema and policy, annotation count and original reference mapping digest. `scripts/validate.py` must refuse an approved commentary with an absent, stale, blocked or Bible-only source report.

**Source validation is not recompilation or publication.** The guard does not extract compiled `RawCom`/`RawCom4`/`zCom`, reconstruct missing authorial XML, verify full native content or certify client rendering. A compiled module has no reliable original XML line numbers; identify any error by provider/module/native key, not an invented source line. Use [production](../PRODUCTION_PIPELINE.md) and [native inspection](../technical/README.md) for subsequent gates.
