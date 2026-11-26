# Bounded French commentary production — issue #587

The source and review policy in [TRANSLATION_HANDOFF.json](TRANSLATION_HANDOFF.json) remains binding. Existing manuscripts are unchanged. Use `progress.json` as the compact task ledger; update it only after saving the matching manuscript and completing the relevant editorial pass. The issue is a human-facing mirror, not input for the language model.

## Connector-accessible cache (no local execution required)

The [generated chapter cache](https://github.com/icfmp/Bible-Resources/tree/work/hmcc-english-chapter-packets/sources/cleaned/commentaries/fr/hmcc-french/editorial/packets) is pinned at commit `354b145094512d69ec5649a39338a9989cd5fe0e`. It contains all 1,189 paired chapters, grouped in blocks of up to ten in JSON Lines files. Each record contains `chapter`, `modern_osis` and `classic_reading`. The index maps each chapter to its file and line. For chapter n, the filename starts at 1, 11, 21, etc. and uses a three-digit chapter number; line number is 1–10 within that book block.

For the next chapter, fetch `packets/Gen.011.jsonl`, line 6 only, from the cache branch. Fetch a range of lines for a bounded batch. Read only the selected records, not the full index or issue. Use exact classic source when the plain-text projection leaves ambiguity. The cache is generated, read-only, and must never be merged into the production branch. Modern fragments are source substrings with the standalone OSIS namespace added; classic readings retain ordered text and reference destinations but are not structural witnesses. The cache was generated through GitHub connector operations from the pinned blobs; its projection is not claimed to be byte-identical to the Python extractor's output.

Verified on both complete frozen blobs: balanced element boundaries, exact source substring roundtrip, 1,189 chapter containers each, identical chapter IDs and order. Verified after commit: 1,189 index entries and bounded retrieval of Gen.16 (8,111 characters). These are extraction checks, not editorial certification. Python tests and final native assembly remain unexecuted.

## Local reproducible extractor

Run from the repository root (the output directory must not yet exist):

```sh
python scripts/commentary_translation_packets.py extract \
  --modern sources/cleaned/commentaries/en/hmcc-modern/hmcc-modern.osis.xml \
  --modern-sha 784dadcb4800c7e8d0fede02aa6116ee55d4f835b25168c4b3ba3ff530e1fb38 \
  --classic sources/cleaned/commentaries/en/mhcc-crosswire/mhcc.osis.xml \
  --classic-sha 6e692fe887b0952bda540599b99c2c39d4b71a9f3d8e32a443db405bf53da52e \
  --output /tmp/hmcc-translation-packets
```

Read only the requested chapter packets. Modern OSIS fragments retain structure and all inline markup; the classic reading projection strips technical wrappers but preserves text order, passage labels and reference destinations. For uncertain cases consult the actual frozen classic XML. The generated manifest identifies non-chapter text; never silently drop it. Generated packets are disposable, reproducible projections, not a second authoritative master.

Translate directly into existing OSIS chapter fragments (no lossy Markdown roundtrip). Use the existing manuscript naming convention and keep all tags, attributes, section boundaries and references. Use the modern source for translation and the classic witness for a separate meaning audit. Do not read the entire issue, prior manuscripts or sources into the model context. Start at Gen.16 (or the current ledger); use batches of 10, increase only when editorial quality and actual context budget permit.

`python scripts/commentary_translation_packets.py check --modern <source> --modern-sha <sha> --manuscripts <directory>` compares native fragment structures; semantic audit and release checks remain separate. The `assemble` subcommand builds a separate, complete editorial OSIS candidate from native fragments. It requires the pinned modern source, an explicitly reviewed target-language OSIS template (including header and all non-chapter content), and all chapter manuscripts. It rejects missing or extra chapters, structure drift and overwriting an existing output. Example: `python scripts/commentary_translation_packets.py assemble --modern <source> --modern-sha <sha> --manuscripts <directory> --template <reviewed-target-template> --language fr --output <new-candidate.osis.xml>`. Target header/metadata and non-chapter editorial decisions remain release-stage obligations; assembly is not editorial or publication approval.

At the end of a batch commit manuscripts and compact ledger. Synchronize the issue without displaying its body:

```sh
python scripts/commentary_translation_packets.py sync --progress sources/cleaned/commentaries/fr/hmcc-french/editorial/progress.json
python scripts/commentary_translation_packets.py sync --progress sources/cleaned/commentaries/fr/hmcc-french/editorial/progress.json --apply
```

The default is dry-run. The command requires authenticated GitHub CLI; it refuses checklist regressions and inventory mismatches. Do not run concurrent issue editors. The connector equivalent can fetch and transform the issue body within one tool execution and emit only counts. Never paste the complete body into the chat. The narrative checkpoint in the issue should be maintained separately or replaced by a link to the current ledger; release gates remain manual.

Initial ledger reconciled against the 15 already checked manuscript files and issue tasks. No change to published sources or French manuscript contents. Tool tests and registry regeneration are required before merging the branch.
