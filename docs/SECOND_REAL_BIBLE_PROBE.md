# Private second real Bible acceptance experiment: WEBP

Issue [#28](https://github.com/icfmp/Bible-Resources/issues/28) requires proving that the generic source/reader tools work on a **different actual Bible** rather than merely on synthetic fixtures or the LSG release.

**Second test edition:** eBible [World English Bible, Protestant-book selection (WEBP)](https://ebible.org/find/show.php?id=engwebp), which the publisher identifies as public domain. The publisher also identifies "World English Bible" as a trademark and requests that changed text not retain that product title. These public-domain and trademark statements **do not themselves approve any transformed release**.

### Original independent publisher inputs

- Official USFX source ZIP: https://ebible.org/Scriptures/engwebp_usfx.zip
- Official SWORD module ZIP: https://ebible.org/sword/zip/engweb2025peb.zip

These are *different artefact lineages*. Both are fetched read-only from the publisher for an isolated, ephemeral GitHub Actions job. Their **actual exact SHA-256** values are computed independently and attached to a metadata-only report. The workflow never commits, republishes, uploads, changes, or installs either Bible into the catalogue.

### Reproducible workflow

The optional GitHub Actions workflow **Review second real Bible (WEBP source and SWORD index)** can be dispatched manually. It also runs for the PR that introduces/changes its workflow or script.

The workflow:

1. Downloads the independently published USFX and original SWORD ZIPs over HTTPS, with no access credentials.
2. Validates safe paths/limits and reads actual original **USFX** books/chapter/verse openings and content fingerprint, without asserting that USFX is OSIS.
2a. Reports all original USFX book identifiers, including any **unnumbered introduction/front-matter books**, as authorial source evidence. Such books are not fabricated into missing verse IDs or silently discarded: their complete text/structure remains an explicit outstanding audit, and they are excluded only from numerical **diagnostics** against ordinary native Bible verse keys.
3. Installs only the independently acquired original provider ZIP into a **private temporary SWORD root** after a complete bounded archive inspection.
4. Compiles the existing generic native SWORD reader against the released system `libsword-dev`; enumerates **real native occupied verse keys**, installed chapter registry and distinct introduction slots. The test requires that this second real source uses `zText`, thereby exercising a different driver from the published LSG `RawText`.
5. Reports book/chapter/verse totals and source-vs-native ordinal count diagnostics; does **not** assume USFM/USFX book codes match OSIS names or that matching counts prove true index/content fidelity. An exact reviewed book mapping is still required for full authorial-reference parity.
6. Uploads **only a text-free JSON evidence file** with exact original-archive hashes and diagnostic counts. The upstream Biblical source and binary are **not** uploaded in any CI artefact.

### Remaining proof requirements

This private smoke can prove the generic native inventory works on a different real module, and can audit the independent original authorial USFX file. **It cannot** certify exact original USFM/USFX → OSIS conversion, note/word/Strong/reference/structure preservation in a compiled module, an Xiphos/AndBible frontend, an approved source version, redistribution of modified text, or another published resource.

The workflow is excluded from everyday repository Validate to prevent an external publisher outage from blocking routine code reviews. Network failures and source changes are independently recorded; after successful first execution, its actual SHA-256 baselines must be reviewed before treating a later upstream download as the same revision.

No second Bible is published by this workflow. No changes to the released LSG 0.1.0 source or SWORD files are authorized or made.
