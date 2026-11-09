# Source-authored OSIS reference inventory (first generic producer)

This tool is the **first independent input producer** for the [stable SWORD verse-index proof](STABLE_SWORD_REFERENCE_AUDIT.md). It is a reusable replacement for extracting *only OSIS-authored numbered verse IDs* with LSG-specific scripts. It accepts any recognized standard OSIS Bible source that uses one unambiguous numeric `book.chapter.verse` ID per verse, including both ordinary `<verse>…</verse>` elements and `sID/eID` milestones.

## Run

After independently validating the **exact** source with the official pinned OSIS 2.1.1 schema and reviewed source policy:

```sh
mkdir -p /tmp/bible-source-proof
python scripts/source_osis_inventory.py \
  --source-osis /path/to/independently-validated-source.osis.xml \
  --keys-output /tmp/bible-source-proof/source-keys.txt \
  --report /tmp/bible-source-proof/source-keys-audit.json
```

Both outputs must be new paths. Original source is read-only. The key list can be passed unchanged as `--source-keys` to `scripts/stable_sword_refs.py` **after the actual installed stable-SWORD registry and an independently collected native reader-key inventory exist**. The receipt binds keys to the **exact input OSIS bytes** with SHA-256; it does not bind them automatically to the publisher's earlier USFM/USFX archive. The import/conversion provenance needs a separately audited source-to-OSIS step before this is called an *original authorial* inventory.

The JSON records only book/chapter/verse identifiers, counts of structure/notes/lexical tags per book, and the tag counts preceding the first numbered verse. It intentionally does **not** contain Bible text, note words, private manuscript data or SWORD binaries.

## Guardrails

- Reject malformed XML, DTDs/entities, foreign verse namespaces, verse milestones without matching `eID`, duplicate or out-of-order references, nested books/verses, malformed book IDs and ambiguous multi-key/range notation.
- Reject an empty source, symlink inputs/outputs, oversized sources, oversized key lists or overwrite of a previous evidence file.
- Do **not** create missing verse identifiers. Internal numeric gaps are reported for editorial investigation, **not treated as missing Scripture or permission to fill a blank**.
- Do not infer structure or verse-zero **compiled** fidelity from these source tag counts. SWORD can store book/chapter introductions in separate verse-zero reader records; inspecting their compiled values remains mandatory.
- The tool does not automatically validate OSIS against the project's pinned official XSD or `SOURCE_VALIDATION.json`, check licensing, inspect a real SWORD reader, check text/punctuation/notes, approve an index compromise or publish anything. The report marks those properties `false`.

## Proof-stage boundary

| Stage | Status |
| --- | --- |
| Original immutable OSIS bytes → source key inventory | Implemented here; synthetically tested |
| Verified USFM/USFX publisher archive → source OSIS | Not delivered by this tool; require independent source conversion/provenance |
| Actual native stable-SWORD reader key inventory + installed registry | **Pending**; never derive from the source list |
| Source key list versus independently collected compiled keys | Existing `stable_sword_refs.py` checker (PR #33) |
| Chapter text, notes, words, lexical and position parity | Pending generalized real-source extraction from historical PR #24 |
| Second different, fully rights-cleared Bible | **Pending**; mandatory to complete issue #28 |
| Editorial and frontend acceptance / release | Separate human/reader/release gates |

The source inventory never automatically updates an already published module's proof or its author-approved version. The released LSG 0.1.0 retains its exact original SHA-bound historical source/reader audit.

See [issue #28](https://github.com/icfmp/Bible-Resources/issues/28) for the remaining producer stages and independent real-edition tests.
