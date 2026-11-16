# Source-attested rebuilt SWORD commentary validation — proposal

**Status:** draft implementation, synthetic validation tests only.
Tracked in [PR #275](https://github.com/icfmp/Bible-Resources/pull/275)
and [release gate #276](https://github.com/icfmp/Bible-Resources/issues/276).
**No approved compiled module currently uses this new mode.**
Owner architecture review and publication authorization are separate.

## Scope

The original compiled CrossWire-derived BRMHCC **0.1.0** retains the
unchanged `stock_reader_keys` path: all six compiled stock members and
every native source entry must be identical to the archived original.

A source-corrected SWORD `zCom` rebuild differs in its compiled members
and potentially in approved source words and navigation keys. The new
`reviewed_compiled_commentary_rebuild` route must therefore be distinct
from (and never relax) the stock-byte identity validator.

## Four evidence inputs

1. **Pinned original.** `config/commentary-intake/<resource>.json` remains
   the original source authority for archived upstream SHA-256, original
   native corpus digest, provider identity and original SWORD version.
   A separate owner-reviewed `config/commentary-rebuilds/<resource>.json`
   must pin the **exact original manifest file SHA-256** and source digest.
2. **Complete source/native comparison.** A source-neutral `SOURCE_AUDIT.json`
   records real `osis2mod` compilation and independent `libSWORD` original
   and rebuilt I/K/TOP native readback, with original and rebuilt complete
   corpus hashes. It separately identifies every source-body correction
   (old/new SHA-256 and **all** original linked keys) and added key/master
   pairs. It asserts that every unrelated original K, every I, both
   opaque TOP records and existing native linked boundaries are preserved.
   The reviewed manifest pins the audit report's **entire exact SHA-256**.
3. **Exact payload.** The review pins the six compiled zCom files plus
   the SWORD `.conf` file. The checker hashes the **actual checked-in
   payload bytes**, rejects extra files, missing members, symlinks,
   stale config and mismatched version, versification or compression
   settings.
4. **Owner approval.** A specific release review records the owner,
   scope and GitHub issue. The approved module must have reviewed
   redistribution/derivative rights. This is separate from its eventual
   exact ZIP/release-plan/publication authorization.

The validator checks internal consistency and exact payload/source/report
hashes offline. It **cannot cryptographically prove that a human really
approved the cited issue or that libSWORD really executed**: those are
independent review and reproducible CI requirements, never to be inferred
from a Boolean in JSON. A fabricated audit/report and self-updated hash
is not evidence of source fidelity.

## What is already tested

Invented-only synthetic tests exercise full payload acceptance and
rejections for changed/extra files, altered original source,
stale audit/proof hashes, false original-I preservation, inconsistent
aliases/counts, aliases referencing new aliases, overlapping edits,
missing owner approval, disguised stock-identical flags, missing
derivative rights and unsafe/missing manifest paths. The unchanged
original-stock proof tests remain in the same suite.

## Remaining gates for BRMHCC 0.1.1

- Owner reviews the generic validation contract and source-comparison
  process **before** any production proof selects this mode.
- Adapt the existing full original SWORD/native private CI to **generate
  an independently reproducible report in this generic schema**, and
  repeat it against the **actual final committed candidate bytes**.
  The earlier ephemeral private ZIP is **not a final release artifact**.
- Check all **28,718 original K**, **1,255 I**, **two TOP**, **24 added K
  aliases**, and **only 12 originally occupied K addresses reflecting the
  two source corrections** (11 linked in Ezekiel 3; 1 in 1 Chronicles 7).
  Compare every original native key, XML structure and linked boundary;
  verify representative installed real-reader navigation.
- Prepare real `SwordVersionDate`, source attribution, licence/rights,
  final deterministic ZIP/checksum and release plan. Obtain **separate
  explicit owner merge/publication permission** before making any public
  GitHub Release or changing the catalogue.

This code is a **proposed verifier**, not a claim that a production
`SOURCE_AUDIT.json` and `SOURCE_VALIDATION.json` already exist for the
unpublished BRMHCC 0.1.1. The original stock and public 0.1.0 stay
immutable.
