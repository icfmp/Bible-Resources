# Editorial rules

Preserve the exact original as immutable input with hash and attribution. Distinguish faithful technical repairs from an optional reader-optimized edition. When a commentary repeats biblical passages, produce an audit report and proposed removal, but **never delete passages automatically**. Textual quotations may be integral to the author's reasoning. Preserve cross references and meaningful emphases.

Warnings: all-caps paragraphs, oversized bold blocks, corrupted numbering, duplicated headings, broken tags, inappropriate fonts/colors, and embedded scripture blocks. Human review decides on ambiguous transformations. Changes must be documented and reversible; provide before/after examples. Do not rewrite theology or the translation during technical cleaning.

## Strict structure handling

Editorial cleanup must never override valid intentional Scripture formatting, including OSIS stanzas (`lg`), poetic lines and their levels (`l`), quotations (`q`), headings, translation additions, the divine name, original emphasis, notes and verse milestones. Unlike advisory typography findings, structural failures are **blocking** and report the source file and line. Never infer whether an unusual case is a mistake: follow [the reviewed OSIS normalization contract](NORMALIZATION_POLICY.md) and add an explicit tested rule before retrying.

## Commentary-specific rules

The official OSIS structure for a commentary is not merely a Bible verse with different words. Preserve the CrossWire commentary entry relationship `div[annotateType="commentary"][annotateRef]`, including book/chapter/range associations, discontinuous references and separate authorial sections. Do not flatten commentary sections, turn quotation material into a Bible passage, infer verse keys, or remove embedded Scripture excerpts merely because the same passage can be read in Bible. The separate fail-closed commentary gate is described in [COMMENTARY_POLICY.md](COMMENTARY_POLICY.md); the original source must survive unchanged.
