# Original witnesses (immutable)

Store only authorized original files under
`sources/original/<type>/<resource-id>/`; permitted types are `bibles`,
`commentaries`, `dictionaries`, `encyclopedias` and `other`.

Preserve exact bytes, original edition identity, checksum, provider URL and
source rights in the resource's provenance. **No normalization in this tree**.
An unknown or restrictive text/annotation license means **do not commit the
file**. Keep an auditable source identity record instead, without a fake
placeholder standing in for actual source bytes.

Compare with the curated master in `sources/cleaned/`; build only from the
approved source and never patch the distributed SWORD binary in place.
See [workspace policy](../../docs/WORKSPACE_LAYOUT.md).
