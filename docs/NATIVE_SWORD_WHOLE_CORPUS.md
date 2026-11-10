# Complete stock SWORD raw-corpus SHA inventory — source-neutral

The goal of [#28](https://github.com/icfmp/Bible-Resources/issues/28) is **independent full source-to-compiled text, notes, explicit links, verse-zero and ordered layout fidelity**. A necessary first compiled-side step is proving we can read and fingerprint **every actual native compiled entry**, not just a few selected verses. This is the purpose of this tool.

## What this stage actually delivers

- `scripts/sword_native_raw_corpus.cpp` iterates the **real released stock libSWORD VerseKey** over the entire configured native versification, with introductory keys enabled. It emits **every occupied numbered verse**, every occupied book/chapter introduction, and separately numbered anonymous TOP entry (if present).
- Its stdout contains **private unfiltered SWORD XML and must NEVER be invoked directly in a CI command, public shell, log or artifact**. Data is length-framed so embedded newlines, tabs and markup cannot corrupt entry boundaries.
- `scripts/sword_native_raw_corpus_inventory.py` captures the C++ stdout **directly into a Python process pipe**. It checks framing, exact byte lengths, no duplicate/unsupported reference IDs, valid UTF-8, bounded entry/corpus sizes, completion totals and explicit non-overwrite of output.
- The Python verifier independently invokes the existing **separate native reference-index inspector** and requires an **identical complete ordered set of numbered keys, intro IDs and occupied anonymous TOP count**. A missing final verse or a skipped introduction blocks the proof.
- Every entry's original raw bytes are SHA-256 digested in memory and discarded. For each book (plus anonymous TOP), the metadata-only JSON reports the **ordered raw-entry manifest SHA-256**, ordinary/introduction counts, first/last original native references and byte totals. A whole-module ordered manifest SHA-256 includes raw bytes from **all** occupied entries. The report is bound to the exact pre/post immutable module payload SHA-256, native driver, v11n, stock engine version and trusted inspector binary hashes.
- Source verse words, Scripture, notes, original XML and compiled SWORD raw content **never appear in the receipt or CI log**.

The ordinary `Validate` workflow now builds and tests the real **published LSG 0.1.0 RawText** compiled module. The optional real [WEBP USFX/zText source research workflow](../.github/workflows/second-bible-proof.yml) additionally hashes all occupied entries of eBible's **actual original, independently SHA-pinned WEBP zText** module. Both compare their corpus counts/ordered keys to independently generated native index evidence.

## Example

Only use the C++ inspector from the Python wrapper. The module must be installed at an isolated SWORD root containing one `mods.d` conf and its `modules` payload.

```sh
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_index.cpp \
  -o /private/sword-native-index -lsword
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_raw_corpus.cpp \
  -o /private/sword-native-raw-corpus -lsword

python scripts/sword_native_raw_corpus_inventory.py \
  --module-directory modules/lsg-1910 \
  --module-id BRLSG1910 \
  --native-index-binary /private/sword-native-index \
  --native-raw-binary /private/sword-native-raw-corpus \
  --report /private/new-text-free-native-corpus.json
```

## What this DOES NOT prove

A SHA fingerprint of *what the compiled module actually contains* **does not prove those bytes are faithful to original publisher Scripture**. The compiler is allowed by SWORD to transform paragraph boundaries, whitespace, verse addresses and encoded notes; two different XML representations can produce the same reader text, and two text-equivalent editions can have different raw-markup hashes.

In particular this stage does **not** yet independently align whole source-versus-compiled text, punctuation, capitalization, footnote bodies/callouts, authored original `osisRef` targets, original Strong/morph word ordinals, poetry/paragraph opening and closing events, supplementary source books or source-edition revision identity. It does not cure the WEBP missing native `Rom.14.24–26` slots; a [separate source-only-word witness](NATIVE_SWORD_RAW_WITNESS.md) found those original word runs in compiled `Rom.14.23` but not their exact complete text/annotations.

It does **not** validate publishing rights or authorize any change to a Biblical source, its approved LSG compiled module or public catalogue. Source-to-compiled semantics, original edition rights, reader compatibility and owner editorial decisions remain distinct review gates.

No changes to published Bible Resource packages, verses, notes or versification are made by this scanner.

## Important corrective note — stock-SWORD reader cursor, 2026-11-10

**Historical PR #48's all-entry raw-content SHA receipts are superseded,
not an independently valid content inventory.** The original C++ raw
enumerator used `hasEntry(&current)` to check each candidate VerseKey
but then called `module->getRawEntry()` **without positioning the module
on `current`**. The SWORD API reads `SWModule::key`, not the separate
pointer supplied to `hasEntry()`. Consequently the stream could carry
distinct correct verse IDs but repeatedly hash a stale module entry,
and the full-corpus metadata digest did not describe the actual ordered
text. The independent **native key index** and existing published
LSG 0.1.0 payload were not altered by this bug.

PR #50 positions `SWModule` for each enumerated `VerseKey` before
reading raw content, then checks the copied key and entry occupancy
again. More importantly, the Python whole-corpus wrapper now accepts
a **second independently compiled** `sword_native_raw_entry.cpp`
exact-key reader. It selects bounded first/intermediate/last canonical
keys from the independently captured index, privately reads those exact
entries and compares their SHA-256 with the full stream. A stale cursor
that repeats one verse in every frame is rejected even when index
inventories and total frame counts appear correct.

This independent second raw reader is **required in repository LSG
RawText and real WEBP zText CI**. A test that merely rehashes the
whole-corpus stream cannot detect this cursor defect. New receipts have
a distinct `independent_native_exact_key_raw_spotcheck_verified` field.
Older recorded raw-corpus hash values must not be treated as compiled
content attestations. References, Bible text, annotations, source
archives and release packages have not been changed.

The corrected private raw hash still does **not** establish original
publisher USFX/OSIS conversion, source-char parity, note anchors,
layout preservation, graphical readers or rights; those remain separate
gates in [#28](https://github.com/icfmp/Bible-Resources/issues/28).
