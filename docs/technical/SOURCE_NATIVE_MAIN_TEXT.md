# Source-to-native main text comparison

Use `scripts/source_native_maintext_probe.py` to compare publisher **USFX numbered-verse text** with actual compiled stock-SWORD text. This is a **read-only diagnostic**, not a general OSIS conversion validator or a release approval.

**Current OSIS-first workflow:** when the reviewed edition has an OSIS authoring master, audit that exact OSIS directly using `scripts/source_osis_inventory.py`, `scripts/osis_semantic_fidelity.py` and the OSIS-to-native candidate and boundary checks. Do **not** convert an approved OSIS master to USFX merely to run the USFX-only probe. Keep this older USFX probe only to verify a genuinely USFX-authored original or independently pinned historical source witness. The source bytes and edition provenance remain authoritative, regardless of the working format.

## Inputs and execution

Pin independently acquired USFX and native SWORD ZIP archives, exact edition identities, their hashes, the reviewed USFM-to-OSIS book crosswalk and the native inspectors. Install the SWORD development library for the C++ inspectors.

```sh
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_index.cpp \
  -o /private/sword-native-index -lsword
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_raw_corpus.cpp \
  -o /private/sword-native-raw-corpus -lsword
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_raw_entry.cpp \
  -o /private/sword-native-raw-entry -lsword

python scripts/source_native_maintext_probe.py \
  --source-usfx-zip /private/original-usfx.zip \
  --original-sword-zip /private/original-sword.zip \
  --crosswalk config/standard_usfm_osis_66.json \
  --native-index-inspector /private/sword-native-index \
  --native-raw-inspector /private/sword-native-raw-corpus \
  --native-entry-inspector /private/sword-native-raw-entry \
  --report /private/maintext-report.json
```

**Privacy:** capture native raw-entry streams only through the tool's private pipe. Never print or upload copyrighted source/native text to Actions logs. The report should contain bounded reference IDs, classifications, counts, sizes and hashes rather than source passages.

## Understand the classifications

The comparison distinguishes exact characters, NFC-only variation, whitespace-only differences, changed punctuation/case, changed word order, unparseable native markup, missing source references and unexpected indexed references. Do not collapse these classes into a single pass/fail string.

USFX source labels and styles are not always authored verse prose: `c`/`v` can represent chapter/verse identifiers, `ve` closes a verse, and `sp` denotes a speaker. Count excluded editorial material separately, including headings, notes and verse-zero data. Unsupported mixed-content structures must be flagged for review, not silently stripped.

An individual native fragment may not be self-contained XML. Report it as unparseable; a tolerant token comparison can assist diagnosis but cannot certify proper native OSIS structure. A second independent exact-key native inspector protects against cursor-position errors that can otherwise repeat one verse's content under different keys.

## Limits

Matching main-text characters does **not** certify note bodies/anchors, Strong and morphology positions, link targets, paragraphs, poetry, quotations, introductions, rights, authorial source edition identity or behavior in Xiphos/another client. Every corresponding [production gate](../PRODUCTION_PIPELINE.md) remains mandatory.

Do not put particular edition's observed counts or one-off study results here; retain them beside its source under `sources/cleaned/**/editorial/evidence/`. For related checks see [native index](SOURCE_NATIVE_INDEX_AUDIT.md), [notes](SOURCE_NATIVE_NOTES_AUDIT.md) and [whole-corpus verification](NATIVE_SWORD_WHOLE_CORPUS.md).
