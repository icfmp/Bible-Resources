# Explicit USFM to native SWORD book-scope index audit

[Issue #28](https://github.com/icfmp/Bible-Resources/issues/28) needs independently produced actual original publisher source and compiled stock-SWORD key inventories. The first WEBP real test found the source ZIP **contains 83 book sections (81 with numbered verses)** whereas the same publisher's labelled 66-book SWORD module exposed only **66 populated books**. Blindly comparing totals or aligning ordinal book positions would be invalid.

## Design: canonical scope is an explicit verified mapping, not a deletion

- `config/standard_usfm_osis_66.json` records the **standard USFM 3-character codes** of the 66 Protestant canonical books and their stock-SWORD OSIS book identifiers. This is a reusable **standard representation crosswalk**, not a WEBP or LSG exception. Source: [USFM Book Identifiers](https://docs.usfm.bible/usfm/3.2/doc/books.html).
- `scripts/source_native_scope.py` takes independently read `(USFM source book ID, chapter, verse)` records, their **original complete book order**, and the actual native SWORD reader key list. It maps only **explicitly enumerated** book identities, checks source/native book presence and order, and compares **individual exact chapter:verse references**.
- The comparator does **not** infer a mapping by book ordinal or by displayed book title. All original source books outside the stated canonical subset are reported **with their exact identifiers and verse counts**, including intro-only books with no numbered verses. Their entire original text/notes/structure remain present in the SHA-pinned source archive and are explicitly **not** verified in this scoped comparison.
- Duplicate source refs, a moved/incorrect native verse, reordered books, missing or unexpected canonical keys, altered book mapping, source keys outside an announced book or ambiguous standard IDs block the scoped reference gate. Even matching total verse counts cannot hide different actual keys.

## Read-only integration

The private, optional [second real Bible workflow](../.github/workflows/second-bible-proof.yml) already downloads publisher original WEBP USFX and actual original SWORD `zText` ZIPs, pinned by previously recorded independent exact SHA-256 values, into temporary Actions storage. It now adds `explicit_standard_book_scope_reference_audit` to the **metadata-only** receipt, plus `standard_66_book_crosswalk_sha256`. The actual original USFX and SWORD assets remain ephemeral and are never added to this repository or uploaded as CI artifacts.

An explicit scoped canonical **verse-key match**, should it occur, is only an index check. It still does **not** establish a matching publisher revision, complete SWORD source-text, lexical markup, note body/anchors, explicit references, intro/poetry/paragraph positions, licensing/redistribution or editorial publication approval. The existing whole-source versus compiled-source **canon discrepancy remains blocked** until its exact provenance and full content are reviewed; no extra USFX books may be silently discarded or represented as missing verses.

The mapping is subject to the real native reader's recorded original book names and order. If a different released SWORD scheme uses different aliases, this audit **fails closed** rather than adding a one-edition exception to get green tests. A separately reviewed mapping/schema version would be required.

## Future required release proof

1. Independently determine the source archive and module's exact edition revisions and book-scope relationship; a canonical subset is not necessarily the complete source.
2. Trace *all* publisher-authorial source material into the intended target OSIS/SWORD scope with separately approved decisions for out-of-scope material and introductions. Preserve source bytes and hashes.
3. Independently extract full actual compiled SWORD text, notes, lexical values, authored explicit links and structural start **and closing** events, including verse-zero and non-addressable intros. Compare against the original edition without deleting annotations or inventing verses.
4. Test a genuinely second complete edition with its actual source, compiler outputs and separate stock-SWORD/reader verification; record licence and owner editorial approval before publication.

See also [SECOND_REAL_BIBLE_PROBE.md](SECOND_REAL_BIBLE_PROBE.md), [SOURCE_OSIS_INVENTORY.md](SOURCE_OSIS_INVENTORY.md), [NATIVE_SWORD_INDEX_INVENTORY.md](NATIVE_SWORD_INDEX_INVENTORY.md).
