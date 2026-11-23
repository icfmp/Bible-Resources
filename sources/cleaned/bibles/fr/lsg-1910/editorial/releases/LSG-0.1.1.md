# Louis Segond 1910 — display-metadata update 0.1.1

**Change requested by the project owner, 2026-11-23:** display
**Louis Segond 1910** (rather than “Louis Segond 1910 - Bible Resources”)
and the short label **LSG1910** (rather than “BRLSG1910”).

The installed SWORD module **still has internal ID `BRLSG1910`**.
The Bible application's library and version chooser use `.conf`
`Description` and `Abbreviation` respectively for these two labels;
the module ID is not the reader-facing abbreviation. No application code,
module directory name or existing installation identity has changed.

## Exactly what changed

Only `Description`, `Abbreviation` and `Version=0.1.1` changed
in `modules/lsg-1910/payload/mods.d/brlsg1910.conf`, plus
versioned catalogue, profile binding and release metadata.
**All four native SWORD RawText data/index members are byte-identical
to the previously source-attested 0.1.0 build**; their hashes are verified
through the source-bound `config/catalogue-import-lsg-0.1.1.json` manifest.
The actual `.conf` SHA-256 is
`37260f8b40edc48ef100c1f738117ac5d384a203e4d995ca8a84414a27805cec`.
Deterministic 0.1.1 ZIP SHA-256:
`383b0493341277ae1776184f13a8f722f48a5bff79566d1993c361229bab404e`
(4,042,083 bytes, five standard SWORD members). These values were
measured on the exact PR checkout in a temporary, read-only GitHub
Actions package fingerprint; the production build/release gate must
independently recheck them.

The approved French reader-profile *text* has not changed: signed
original source Git blob
`9d13c0735a079f8853c0169270b2a31493621eab`;
only its compatible module-version binding and current release URL
have been advanced.

## Independent OSIS structure inspection

Read-only inspection of the exact approved
`sources/cleaned/bibles/fr/lsg-1910/lsg-1910.osis.xml`,
previously approved SHA-256
`d6abd7416d026c86ce2e9577e3bfe7a10159c5c78d236913359c7fab013449d0`
(29,686,495 bytes), confirms:

| Feature | Observed |
| --- | ---: |
| Book divs | 66 |
| Chapter start IDs / matching end IDs | 1,189 / 1,189 |
| Verse start IDs / matching end IDs | 31,170 / 31,170 |
| Duplicate/unmatched verse or chapter IDs | 0 |
| Lemma/Strong word markup elements | 705,728 |
| Notes | 9,751 |
| Reference elements | 19,679 |
| Poetic line elements | 23,991 |

Original `Mark.10.53` remains in the OSIS following `Mark.10.52`
despite the approved stable Segond native reader-index combination in
one Mark 10:52 entry. `Job.34.37` is absent from the eBible source and
has not been invented. This is a structural inventory and check
against pre-existing signed fidelity/native receipts, **not** a new
independent print-edition textual collation or Xiphos visual approval.
The existing note-spacing/introduction literal-formatting caveats
remain unchanged.

Original eBible source ZIP SHA-256:
USFM `64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900`,
USFX `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`.
No original archive, approved OSIS, verse, note, cross-reference,
source identity, license or versification was modified.

## Publication and historical integrity

[0.1.0 historical release](https://github.com/icfmp/Bible-Resources/releases/tag/lsg-0.1.0)
remains immutable. **Its versioned GitHub Release ZIP** was
`af2f80ea84f40a6bf62993c9e65c2e2061e1ec20b34b0772a4eb775dd47723c1`
(3,881,106 bytes), while the **0.1.0 Pages ZIP** was
`f3f74a1016f708e10263b5628e606a73b727c0e80fbb7e131d195c4b11d86c51`
(4,042,088 bytes). These historical ZIPs differ; see
[release QA #271](https://github.com/icfmp/Bible-Resources/issues/271).
They must never be overwritten or falsely described as identical.
The 0.1.0 source audit and approval manifest remain preserved.

The current 0.1.1 release uses one explicit current release plan
instead of the 0.1.0 frozen historical publication exemption.
A versioned 0.1.1 GitHub Release is **not** established by this
report or a test alone. After approval, the single Pages publishing
workflow verifies it and the public HTTPS catalogue independently.
Users with the old installed 0.1.0 configuration will see the new
labels **only after updating/reinstalling** the module.

Remaining limitations and provenance are in the
[original 0.1.0 editorial record](LSG-0.1.0.md).
