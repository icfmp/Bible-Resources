# OSIS semantic fidelity

OSIS validity is necessary but not sufficient: two schema-valid files can differ in wording, annotation meaning or structure. Compare the **entire** original and cleaned resources before approving a transformation.

## Run a source-to-candidate audit

Validate each input against the pinned official OSIS schema first. Run the generic analyzer on independently pinned files:

```sh
python scripts/osis_semantic_fidelity.py \
  --source-osis /private/original.osis.xml \
  --candidate-osis /private/cleaned.osis.xml
```

Check the script's actual `--help` and repository tests before incorporating it into automation; do not infer that the illustrative invocation proves every kind of fidelity.

## Required proof

- Preserve native references and authorial identifiers, including book order, verse omissions, commentary scope and versification.
- Report textual differences (words, case, punctuation), structural differences (paragraphs, poetry, headings, quotations), annotations, hyperlinks and their literal targets independently.
- Keep the original unchanged; record exactly which rules produced every changed entry, why the rule is permissible, and how it can be undone.
- Flag ambiguous structures and unsupported constructs rather than auto-repairing them.

OSIS source parity does **not** establish native SWORD parity, a correct reader rendering, rights, source edition identity or publication approval. Complete the remaining [production gates](../PRODUCTION_PIPELINE.md) and use the [technical verification guides](../technical/README.md).

Edition-specific reports and unresolved decisions belong beside the reviewed resource. This policy contains no publication status or historical test results.
