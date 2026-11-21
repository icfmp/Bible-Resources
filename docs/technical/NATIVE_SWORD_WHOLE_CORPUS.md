# Native SWORD whole-corpus inventory

**Purpose:** independently inspect and fingerprint **every populated native SWORD entry**, including numbered passages, book/chapter introductions and anonymous TOP records. A whole-module raw hash establishes what compiled bytes are read, **not** their source fidelity.

## Secure procedure

- Compile the repository's `scripts/sword_native_index.cpp` and `scripts/sword_native_raw_corpus.cpp` against a released stable `libsword-dev`, and pin the binaries.
- **Never invoke the raw-corpus C++ binary directly in public shell logs or CI:** it outputs private unfiltered native markup. `scripts/sword_native_raw_corpus_inventory.py` captures length-framed output in a private pipe and publishes only metadata/hashes.
- Use an isolated, exact-source-pinned SWORD root and module ID. The wrapper rejects malformed framing, duplicate/unordered native identifiers, invalid UTF-8, mismatched entry lengths, unexpected index/TOP counts and unsafe output paths.
- Independently read the real native key/index inventory and require matching ordered numbered keys, introductions and TOP occupancy. Hash every native entry in memory, with per-book and whole-corpus ordered SHA-256 receipts bound to the exact payload, driver, versification, engine and inspectors.
- **Mandatory cursor safety:** `SWModule::getRawEntry()` depends on the module's current key, not merely a `VerseKey` pointer passed to `hasEntry()`. The native reader must position the module before reading. A *second, independently compiled* exact-key raw inspector (`scripts/sword_native_raw_entry.cpp`) must spot-check bounded first/middle/last references so a stale cursor cannot yield repeated content under distinct keys. Historic receipts from before that fix must **not** be used as content attestations.

## Example on an isolated module

```sh
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_index.cpp \
  -o /private/sword-native-index -lsword
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_raw_corpus.cpp \
  -o /private/sword-native-raw-corpus -lsword
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_raw_entry.cpp \
  -o /private/sword-native-raw-entry -lsword

python scripts/sword_native_raw_corpus_inventory.py \
  --module-directory /private/module \
  --module-id MODULE_ID \
  --native-index-binary /private/sword-native-index \
  --native-raw-binary /private/sword-native-raw-corpus \
  --native-entry-binary /private/sword-native-raw-entry \
  --report /private/new-native-corpus-receipt.json
```

The independent exact-key binary is supplied here because the whole-corpus stream alone cannot detect a stale SWORD cursor. Confirm the resulting report's `independent_native_exact_key_raw_spotcheck_verified` and `exact_all_occupied_native_keys_matched_independent_index` flags. This is an example command, **not** a claim that this run has executed or that the authored source matches.

## Proof boundary

A complete raw-corpus digest cannot prove source wording/punctuation, note callers, references and their targets, Strong/lemma ordinal alignment, verses absent by textual decision, poetry and paragraph positions, licensing or reader display. These require separate [source/native text](SOURCE_NATIVE_MAIN_TEXT.md), [notes](SOURCE_NATIVE_NOTES_AUDIT.md), [index](SOURCE_NATIVE_INDEX_AUDIT.md) and [reader/release](../PRODUCTION_PIPELINE.md) gates.

Resource-specific historical observations, raw-hash supersession and corrections must be retained in edition evidence or relevant GitHub issue/PR, not used as general current instructions.
