# Combined independent OSIS → stock SWORD numbered-key audit

Issue [#28](https://github.com/icfmp/Bible-Resources/issues/28) requires a
repeatable source→compiled pipeline rather than hand-paired evidence.

The read-only \`scripts/source_native_index_audit.py\` composes the existing
**independent** \`source_osis_inventory.py\` and actual stock-engine
\`sword_native_inventory.py\` producers, using the generic
\`stable_sword_refs.py\` checker. This stage audits **only exact numbered
verse-key parity**. It does not fix or add missing verses.

## Use

Start from a **separately validated source OSIS** and an actual isolated SWORD
module tree containing a \`payload/\` directory. Compile the already-reviewed
stock index inspector against a released libsword:

\`\`\`sh
g++ -std=c++17 -O2 -I/usr/include/sword scripts/sword_native_index.cpp \
  -o /private/sword-native-index -lsword
python scripts/source_native_index_audit.py \
  --source-osis /private/original-validated.osis.xml \
  --module-directory /private/module \
  --module-id MODULE_ID \
  --native-index-binary /private/sword-native-index \
  --report /private/new-index-receipt.json
\`\`\`

The report must not already exist and cannot be placed inside the compiled
module. It includes the exact source OSIS SHA, independent source key digest,
native installed module digest, stock inspector digest, native driver/v11n,
reader/registry key digests, keyed mismatch samples, occupied intros and the
number of otherwise nonaddressable TOP entries. All source and module inputs
are checked again after native readback. No source Scripture content or notes
are emitted to the report.

A successful exit means **exact source-OSIS versus stock-native numbered
reference index only**. Differences exit nonzero and still write a bounded
diagnostic report; the tool refuses overwritten evidence. The generic checker
has a separate source-bound *reviewed merge* pathway: this combined initial
command intentionally supports **exact parity only** and fails closed when
there are legitimate but separately reviewed versification merges (e.g. the
published LSG 0.1.0 historical exception). Do not change that release or
silently ignore the source-only references to make this command pass.

## Explicit limitations

- Original publisher **USFM/USFX → OSIS** provenance, rights and exact edition
  identity must be independently established; a parsed OSIS input is not
  automatically proof of the publisher's original edition.
- Full native compiled words/punctuation, notes/callers/word anchors,
  Strong/lemma ordinals, explicit cross-reference targets, verse-zero text,
  title/paragraph/poetry opening and closing, and standalone/parallel
  reader behavior remain **unverified**.
- Complete editorial review, publication approval and the release receipt
  are separate requirements. All such booleans remain false by design.
- The synthetic tests mock the stock reader producer; existing *separate*
  GitHub CI workflows exercise actual published LSG RawText and original WEBP
  zText native inventories. This command alone is **not yet end-to-end
  exercised on two independently converted same-edition Bibles**.

No published module, public catalogue, Scripture, annotation, source archive
or edition identity is changed by this addition.
