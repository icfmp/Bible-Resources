# Editorial rules

Preserve the exact original as immutable input with hash and attribution. Distinguish faithful technical repairs from an optional reader-optimized edition. When a commentary repeats biblical passages, produce an audit report and proposed removal, but **never delete passages automatically**. Textual quotations may be integral to the author's reasoning. Preserve cross references and meaningful emphases.

Warnings: all-caps paragraphs, oversized bold blocks, corrupted numbering, duplicated headings, broken tags, inappropriate fonts/colors, and embedded scripture blocks. Human review decides on ambiguous transformations. Changes must be documented and reversible; provide before/after examples. Do not rewrite theology or the translation during technical cleaning.

## Strict structure handling

Editorial cleanup must never override valid intentional Scripture formatting, including OSIS stanzas (`lg`), poetic lines and their levels (`l`), quotations (`q`), headings, translation additions, the divine name, original emphasis, notes and verse milestones. Unlike advisory typography findings, structural failures are **blocking** and report the source file and line. Never infer whether an unusual case is a mistake: follow [the reviewed OSIS normalization contract](NORMALIZATION_POLICY.md) and add an explicit tested rule before retrying.

## Commentary-specific rules

The official OSIS structure for a commentary is not merely a Bible verse with different words. Preserve the CrossWire commentary entry relationship `div[annotateType="commentary"][annotateRef]`, including book/chapter/range associations, discontinuous references and separate authorial sections. Do not flatten commentary sections, turn quotation material into a Bible passage, infer verse keys, or remove embedded Scripture excerpts merely because the same passage can be read in Bible. The separate fail-closed commentary gate is described in [COMMENTARY_POLICY.md](COMMENTARY_POLICY.md); the original source must survive unchanged.

## Consult the original printed edition when available

For either a Bible or a commentary, **prefer the original printed edition (PDF or faithful facsimile) as an editorial layout reference** before inventing paragraph or poetry divisions. Identify the exact author, work, language, translator, publisher, edition/year and any revision; distinguish a genuinely matching source edition from a later reprint, abridgment or translation. Cite the PDF's stable origin, edition metadata, page numbers and the corresponding SWORD module keys in the review log.

Compare authorial paragraph boundaries, titles, indentation, quotations, verse divisions, poetic lines/stanzas, lists, and commentary section breaks. If a reliable printed original confirms a structure lost during conversion, propose its restoration in standard OSIS with a text-preserving, reviewed and tested transformation. **Do not assume a modern PDF has the original layout**, and do not transplant paragraphs from an edition that does not match the module. When the PDF is missing, unreadable or contradictory, flag the precise passage for review rather than silently guessing.

The PDF is **evidence for editorial reconstruction, not automatically a licensed distributable source**. Record access/provenance and rights separately; never commit or redistribute a copyrighted PDF or edition without permission. Keep the original module intact and log source-to-output changes with page/key references. PDF page numbers refer to the printed source, not to original XML source line numbers.
