# Main text fidelity policy

**Canonical rule:** preserve the identified edition's exact authored words, punctuation, case, verse identities and ordering. Whitespace or encoding adjustments are acceptable only when proven layout-only, documented and reversible. An apparent source typo requires independent source-attested editorial review; never silently "correct" it.

## What to compare

- Pin the exact original source and the reviewed cleaned candidate with immutable hashes and source identity.
- Compare **all** canonical numbered passages at their native references; capture omissions, insertions, changes, duplicate keys, source-specific versification and verse-zero content separately.
- Distinguish normalized whitespace from changes in letters, case, punctuation, words, verse IDs, order or commentary coverage.
- Verify structural material (paragraphs, poetry, notes, cross-references, titles, introductions and lexical markup) separately. A whole-text digest or unchanged word list cannot prove structural fidelity.
- When comparing with an upstream compiled SWORD module, verify its exact identity and native readback. A stock binary may be an independent witness, but it is not automatically authoritative over the identified print/source edition.
- Produce complete per-key exceptions, original/cleaned/native hashes and an approved decision ledger. Unexplained mismatches fail closed.

## Reusable evidence

Use [source-native main text verification](../technical/SOURCE_NATIVE_MAIN_TEXT.md), [native SWORD whole-corpus inspection](../technical/NATIVE_SWORD_WHOLE_CORPUS.md), [versification policy](VERSIFICATION_POLICY.md) and the [production contract](../PRODUCTION_PIPELINE.md).

Exact test-run numbers, edition-specific mismatches and source witness comparisons belong under the affected edition's `sources/cleaned/**/editorial/evidence/` directory. A successful historical pilot is not a reusable release authorization.
