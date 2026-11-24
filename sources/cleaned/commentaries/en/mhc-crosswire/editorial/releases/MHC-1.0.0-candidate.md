# Matthew Henry's Complete Commentary — MHC 1.0.0 candidate (not a release)

The approved 0.1.0 original, cleaned master, binary package and catalogue remain unchanged.

## Reproducible proof

- [Published-source and native audit](https://github.com/icfmp/Bible-Resources/actions/runs/45437564914) authenticates the actual public 0.1.0 ZIP and the full source/native scope; 4,255 numbered groups and one reclassified chapter preface.
- [Exact reference-only and boundary proof](https://github.com/icfmp/Bible-Resources/actions/runs/45442479885): all six previously flagged boundary cases are exact nonwhitespace character matches including the original closing material; ten inherited surrounding reference spaces affect exactly 88 native frames, with no other XML or text change. #295 closed.
- [Independent CCEL witness comparison](https://github.com/icfmp/Bible-Resources/actions/runs/45444013587) proves all 781, 642 and 469 witness word tokens in the three adjacent native masters. Its later paragraph census failed on a comment node; the completed comparison and receipt are retained.
- [Full native alias trial](https://github.com/icfmp/Bible-Resources/actions/runs/45447586839): source-only extension of three existing `osisID` scopes, all original labels (`n`), pairing keys, prose and paragraph/poetry markup retained. 31,101 K, 1,255 I and two TOP; three additional genuine links, no change to previous raw frames compared with the whitespace-only candidate. Exact XSD validated. Candidate source SHA-256 `069d18e5be5839e3082fbdd33280802c5287b0d5be2703cb0494f4c29f1f4749`; native corpus SHA-256 `4e6efd6b9374bbac5185b51abf0bced8791ea59fa87f098504f71dce8ce36928`. Artifact 14944829878, SHA-256 `db179a533e43f0ba90682ad1786fb4c674cbd5a9db8d2a98b2d34acc89b7efe2`.
- Independent reader verification: [run 45449046710](https://github.com/icfmp/Bible-Resources/actions/runs/45449046710) PASS; all nine real Xiphos and diatheke passages, including the three repaired alias/master pairs. No universal GUI or clicked-reference claim.

## BRNP representation decision

The current draft BRNP canonical target requires annotated `div` containers. All 4,255 existing MHC paired verse scopes cross XML parent boundaries; 4,254 have visible material before their start within the same parent. Their common ancestor is a book or introduction containing multiple scopes, never a single-owner section container. Nineteen pairs involve poetry-line boundaries. Direct annotated-div milestone substitution is rejected by the pinned official schema; wrapping existing common ancestors would misassign multiple commentary sections, and splitting authorial paragraphs or poetry is not a lossless normalization.

The remaining `NO_COMMENTARY_ENTRIES` diagnostic remains explicitly open under #451. It is a representation discrepancy, not a missing-content or invalid-OSIS finding. Owner approved development of a **generic explicitly reviewed alternative paired-verse-milestone profile**, with independently validated unique canonical scope members, book/chapter ownership, balanced nonoverlapping pairing, source and reader parity; the current default checker is unchanged. The draft implementation is under regression review. Making the profile mandatory is a separate decision. Do not insert artificial annotations or suppress the finding.

## Release boundaries

Do not close #290 before the exact reviewed candidate is integrated and independently reader-tested. The owner requested version 1.0 (stored as SemVer 1.0.0), display name Matthew Henry's Complete Commentary and short name MHC. Preserve the existing SWORD identifier MHC and edition ID. Publication is contingent on validation; do not modify prior immutable release bytes. Preserve all historical proof and release bytes; bind any new release manifest to the original, previous reviewed source, exact reversible attribute edits, previous/current native bodies, reader receipt and final payload hashes.
