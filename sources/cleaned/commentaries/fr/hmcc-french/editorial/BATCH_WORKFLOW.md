# Bounded French commentary production — issue #587

The source and review policy in [TRANSLATION_HANDOFF.json](TRANSLATION_HANDOFF.json) remains binding. Existing manuscripts are unchanged. Use `progress.json` as the compact task ledger; update it only after saving the matching manuscript and completing the relevant editorial pass. The issue is a human-facing mirror, not input for the language model.

## Read only the current batch

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

`python scripts/commentary_translation_packets.py check --modern <source> --modern-sha <sha> --manuscripts <directory>` compares native fragment structures; semantic audit and release checks remain separate. Full assembly and final OSIS header/metadata decisions remain a release-stage operation, not an automatic acceptance of the fragments.

At the end of a batch commit manuscripts and compact ledger. Synchronize the issue without displaying its body:

```sh
python scripts/commentary_translation_packets.py sync --progress sources/cleaned/commentaries/fr/hmcc-french/editorial/progress.json
python scripts/commentary_translation_packets.py sync --progress sources/cleaned/commentaries/fr/hmcc-french/editorial/progress.json --apply
```

The default is dry-run. The command requires authenticated GitHub CLI; it refuses checklist regressions and inventory mismatches. Do not run concurrent issue editors. The connector equivalent can fetch and transform the issue body within one tool execution and emit only counts. Never paste the complete body into the chat. The narrative checkpoint in the issue should be maintained separately or replaced by a link to the current ledger; release gates remain manual.

Initial ledger reconciled against the 15 already checked manuscript files and issue tasks. No change to published sources or French manuscript contents. Tool tests and registry regeneration are required before merging the branch.
