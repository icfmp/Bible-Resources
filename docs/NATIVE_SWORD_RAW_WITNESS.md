# Native SWORD raw-entry presence witness (source-only verse IDs)

This is a **private diagnostic** for [issue #28](https://github.com/icfmp/Bible-Resources/issues/28), not a translator, a new versification scheme or a substitute for full source→compiled-content parity.

The [standard USFM↔native OSIS key comparison](SOURCE_NATIVE_BOOK_SCOPE.md) revealed three authorial WEBP references whose native KJV `zText` index has no ordinary verse slots: `Rom.14.24`, `Rom.14.25`, `Rom.14.26`. **Do not infer missing text from missing index keys, or infer retained text from the documented `osis2mod` fallback behavior.**

The new implementation is completely edition-neutral:

- `scripts/sword_native_raw_entry.cpp` asks a **released stock libSWORD engine** for the **exact supplied occupied native verse ID**, requiring exact key round-trip. It supports ordinary `RawText` and `zText` Bible drivers. Its stdout contains unfiltered original Scripture XML and must **never be invoked directly in CI logs or copied into a publication/report**.
- `scripts/sword_missing_verse_witness.py` independently inventories source USFX and the actual original SWORD module in a **temporary isolated `SWORD_PATH`** and uses a reviewed standard-book identifier crosswalk. It obtains the source-only IDs from the **exact generic crosswalk difference result**—no hardcoded verse exceptions. For each missing reference, it finds the **nearest preceding actual occupied reader slot within that same native book and chapter**, then invokes the raw helper privately, capturing its entire stdout bytes **in memory**.
- It extracts the source-authored verse's visible word tokens separately from footnote/cross-reference text and compares their full contiguous sequence with word tokens in the unfiltered native entry, omitting that entry's footnotes for the diagnostic. It records SHA-256 identities, token lengths, presence/absence, native slot ID and relative position **without including the original source's words, notes, punctuation or module's raw XML**. Original ZIPs remain read-only, the temporary files are discarded, and the original module bytes are hashed before and after inspection.
- A missing word run is classified **`source_word_run_not_found_in_preceding_native_entry`**, not automatically "lost Scripture" (it may be stored in another location or the editions may differ). A present word run is **`contiguous_source_word_run_found_in_preceding_native_entry`**, not a certified faithful or complete verse: punctuation, capitalisation, spacing, structural/notes/lexical attributes and authored numbering could still be different. Ambiguous or too-short source entries cannot establish a positive witness.

## Reproduce on independently sourced stock SWORD

The optional [second real Bible research workflow](../.github/workflows/second-bible-proof.yml) compiles both C++ readers against system `libsword-dev` and downloads the two **previously SHA-pinned** official eBible WEBP research archives. It then performs:

```sh
python scripts/sword_missing_verse_witness.py \
  --source-usfx-zip /private/original-publisher-usfx.zip \
  --original-sword-zip /private/original-publisher-sword.zip \
  --native-index-inspector /private/sword-native-index \
  --native-raw-inspector /private/sword-native-raw-entry \
  --crosswalk config/standard_usfm_osis_66.json \
  --report /private/new-metadata-only-raw-witness.json
```

**Never** call `sword-native-raw-entry` directly in a terminal that sends stdout to a public log or CI artifact. The Python wrapper is the only approved runner here: it captures raw bytes privately and persists **metadata only**. It also refuses to overwrite the report.

The complete authorial source XML and compiled SWORD content are **not** exported by the workflow; only the metadata-only witness report and independent original source/native index report are uploaded. Source/SWORD text differences in other books, omitted introductions and all 17 extra original USFX sections remain outside this narrow diagnostic.

## Limits and follow-up

A positive word-run match is **evidence of lexical presence in a native raw entry**, not full text fidelity. The project still needs exact original-edition/revision provenance, authorial USFM/USFX→OSIS conversion fidelity, complete SWORD character/punctuation/word-ordinal/note body/anchor/explicit target/ordered structural boundary and verse-zero audits, and separate human/editorial and reader acceptance. No text is renumbered, merged, removed, introduced or authorised for publication by this experiment. Both the original public LSG 0.1.0 module and the public catalogue remain unchanged.

See CrossWire's official [osis2mod](https://wiki.crosswire.org/Osis2mod) documentation for the *possible* append behavior with an out-of-versification source key. Its general behavior does not replace an **actual module readback**.
