# Private USFX → stock-SWORD main-text character comparison

Issue [#28](https://github.com/icfmp/Bible-Resources/issues/28):
independently test **source main-Scripture characters and punctuation against
actual compiled stock-SWORD content**, rather than assuming that matching
verse indices or a compiled-raw SHA means textual parity.

## Scope

`scripts/source_native_maintext_probe.py` consumes independently obtained
publisher **USFX source** and **stock SWORD** module archives. The source
archive is read by the existing safe, source-identity-hashing importer;
the compiled archive is reinstalled privately in a temporary isolated SWORD
root and scanned using the *released* libSWORD `RawText`/`zText` engine.
The existing full-corpus C++ inspector emits length-framed raw entries **only
to a captured private Python pipe**. It must never be invoked directly in
GitHub Actions shell logs.

A new optional, in-memory observer in
`sword_native_raw_corpus_inventory.py` receives each verified raw entry;
the original whole-corpus SHA and independently verified stock native
index remain unchanged. It never persists or prints entry content.

For the explicit reviewed USFM↔OSIS book crosswalk, the tool independently
parses publisher USFX chapter/verse markers and compiled OSIS-fragment
characters **for each actually indexed canonical verse**. Note and
cross-reference note bodies and standalone headings are explicitly excluded
from the *main-verse character* lane and counted separately; the remaining
source/compiled text and punctuation are compared as Unicode semantic text
(after XML entity parsing, **without fixing character content**). Results
distinguish:

1. Exact semantic characters including punctuation, case and whitespace.
2. NFC-only differences.
3. Whitespace-only differences.
4. Same ordered words, changed punctuation/spacing.
5. Same folded words, changed case/punctuation.
6. Changed word sequence.
7. Unparseable or non-self-contained native OSIS fragments.
8. Unindexed source-only verses and unexpected native indexed verses.

The report is **metadata only**: SHA-256s of exact original archives,
source XML, module payload, native inspectors, stock full raw corpus,
numeric counts, classifications and at most 25 reference IDs / character
counts / hashes (no Scripture, footnote text or native XML). A changed
source/archive or mutated compiled module rejects the report. Original
archives and public modules are unchanged.

## Private original-edition research run

```sh
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_index.cpp \
  -o /private/sword-native-index -lsword
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_raw_corpus.cpp \
  -o /private/sword-native-raw-corpus -lsword
python scripts/source_native_maintext_probe.py \
  --source-usfx-zip /private/original-authorial-usfx.zip \
  --original-sword-zip /private/original-compiled-sword.zip \
  --crosswalk config/standard_usfm_osis_66.json \
  --native-index-inspector /private/sword-native-index \
  --native-raw-inspector /private/sword-native-raw-corpus \
  --report /private/new-maintext-metadata-only.json
```

The optional pinned-real-WEBP CI workflow runs this on the *existing*
independently SHA-pinned eBible publisher USFX and corresponding actual
zText ZIP. Do not modify the crosswalk, source references or published
LSG to force a match. The known source-only `Rom.14.24–26` verse keys and
17 extra authorial source book sections remain reported and **block full
source fidelity** even when some indexed verse characters match.

## Strict limitations

- This is **source USFX main-numbered-verse text → actual compiled raw
  fragment main text**, not a validation of the intermediate
  USFM/USFX→OSIS conversion or proof that two provider archives represent
  the same exact editorial revision.
- A SWORD raw fragment may be syntactically non-self-contained; such a
  verse is classified **unparseable**, not silently repaired/accepted.
  Different whitespace, markup and authored letter case are not normalized
  away for the exact test. No result claims the publisher's original
  **XML bytes** are identical to native XML bytes.
- Source extra/noncanonical books, headings, book/chapter intros and
  verse-zero contents remain independently unverified; exclusions are
  counted and are **not approved omissions**. The source USFX headings and
  compiled OSIS titles may have different storage.
- **Notes** (caller, type, body, anchor), Strong/morph lexical attributes,
  authored cross-reference targets, structure/poetry opening and closing
  positions, source rights, graphical/parallel readers and human editorial
  sign-off each need separate proof stages.
- A diagnostic script can finish and report **BLOCKED** on expected
  differences; zero process exit is only completion of the **read-only
  diagnostic**, never a publication gate. Use the report's scoped status.

No full edition or third-party text is authorized for public redistribution
by the mere existence of this diagnostic.
