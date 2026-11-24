# Bible J. N. Darby (2024) — 0.1.2 candidate

**Status: draft; not published; final technical evidence and explicit owner publication authorization required.**

## Scope

- Correct the unregistered `GlobalOptionFilter=OSISXRefs` to the registered `OSISScripref` (#553, PR #554).
- Display name: Bible J. N. Darby (2024); abbreviation: `DARBY2024`. The installed module ID `BRJND2024`, driver `zText` and Luther versification remain unchanged.
- Preserve the exact BPC 2024 revision 2.0 original and approved cleaned OSIS, including all intentional omissions and existing documented reversible editorial overlays. No new editorial changes are proposed.
- The intended candidate changes only the configuration member of the native ZIP. Verify against the immutable 0.1.1 asset before acceptance.

## Evidence and acceptance

Original BPC OSIS SHA-256: `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`.
Approved cleaned OSIS SHA-256: `35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d`.
Previous canonical archive SHA-256: `2b48c3c9a8897e58805a7cb3be731bb895363e51bc854df502ce7e7a45f0c2c4`.

The historical 0.1.1 source/native audits and bounded Xiphos/AndBible review remain applicable to the unchanged source and binary content, but are not new 0.1.2 visual or option-mode acceptance. See [the previous reader evidence](../evidence/darby-2024-0.1.1-final-reader-qa.md).

Required before publication: actual archive and member hashes, renewed source-to-native index/structure/note audit, catalogue and release coverage, default and explicit cross-reference mode tests, reader acceptance or documented limitations, all required CI checks, and explicit owner publication authorization. Issue #549 remains open independently; do not claim that correcting the filter resolves optional-mode plain-text XML leakage.

The immutable 0.1.1 release remains available for rollback. No application repository change.

## Verified candidate result

- Canonical diagnostic ZIP SHA-256: `009af5d19795797337cfa25b68ce96d593fe60f93770d01c44942455d6827e5d` (1960800 bytes); production builder must independently match it.
- Candidate installed payload SHA-256: `37672ac52e881cf8343412eae65090c2eb745be7027896f10872140f248bb429`.
- Independently downloaded immutable 0.1.1 asset matched its pinned checksum. Only `mods.d/brjnd2024.conf` differed; all six compiled data files were identical.
- Complete native audit: 31,166 numbered verses, 6,340 note bodies/callers/types/anchors/target sequences, 1,257 titles (including two outside-book titles), 5,197 paragraphs, 3,895 poetry lines, 708 poetry groups; all 1,041 explicit target attributes addressable. No numbered reference or note discrepancy.
- Diatheke: 13 sampled references, default and cross-references enabled, no literal OSIS tags in either result. This is a bounded test, not full graphical-reader or upstream #549 resolution.
- [Machine-readable evidence](../evidence/darby-2024-0.1.2-native-audit.json) from [CI](https://github.com/icfmp/Bible-Resources/actions/runs/45376786567). That run was superseded after emitting the Darby results; no overall green CI claim.
