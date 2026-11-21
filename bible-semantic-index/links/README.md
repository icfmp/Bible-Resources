# BSI links — future dictionary and encyclopedia crosswalks

This is the reserved home for **small, separate, source-verified indexes connecting BSI entities to external resources**. No dictionary content is copied here, and no links are claimed to have been reviewed yet.

The BSI core lookup identifies exact MACULA original-language words. MACULA may additionally provide lemmata, Strong or other lexical features, but those do **not** prove that an external dictionary entry represents a unique individual, place, or contextual sense. Do not generate links solely from identical spelling, Strong IDs, or a guessed verse match.

## Storage convention

Use one reviewed file per **resource edition**, for example:

```text
links/
  README.md
  schema.v1.json
  dictionaries/
    README.md
    <resource-id>-<edition>.json
  encyclopedias/
    README.md
    <resource-id>-<edition>.json
```

The files are *mapping tables only*, with stable BSI `entity_id`, exact external `entry_id`, explicit `relation` and source-specific evidence. They must record licensing, revision, editorial review status and unambiguous resource identity. A missing mapping means **unknown**, not an automatic match.

Use `schema.v1.json` to validate the future file format. The directories are deliberately empty of live links until the first dictionary/encyclopedia edition has been inventoried and its rights checked. Key Terms are excluded from the current BSI v0.1 scope.
