# Source-attested rebuilt SWORD commentary validation — accepted architecture

**Status:** architectural choice accepted on 2026-11-16 under the project
owner's delegated technical decision, without publication or merge approval.
Implemented in [draft PR #275](https://github.com/icfmp/Bible-Resources/pull/275)
and technically verified by [1,329 unit/regression tests](https://github.com/icfmp/Bible-Resources/actions/runs/43867792317)
and the [complete private libSWORD/Xiphos audit](https://github.com/icfmp/Bible-Resources/actions/runs/43867792111).
Tracked for final release readiness in
[issue #276](https://github.com/icfmp/Bible-Resources/issues/276).

**No approved rebuilt module currently uses the new mode.** A source-attested
private rebuild is **not** a reviewed final release package. Independent
source/rights review, an exact final release payload, and express owner
merge/publication permission remain mandatory.

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

- **Architecture selected and pilot implemented**. The full private
  original-to-rebuild proof generator now emits metadata-only, explicitly
  unapproved draft records from actual SWORD/native reader evidence.
- **Remaining:** independently review that evidence and regenerate the
  finalized proof and all file digests against the **actual final committed
  candidate**. The ephemeral private ZIP is not a final release artifact.
  The offline proof validator checks pinned claims and exact bytes; it
  cannot replace independent evidence provenance and human approval.
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

## Native member naming follows SWORD BlockType

The published original `BlockType=BOOK` uses six `{nt,ot}.bzs/.bzv/.bzz` members. The standard `osis2mod -b 3` private recompilation has `BlockType=CHAPTER` and six `{nt,ot}.czs/.czv/.czz` members; verse-block modules use `{nt,ot}.vzs/.vzv/.vzz`. The new validator derives its **complete six-member inventory** from the candidate's checked `BlockType` instead of requiring the original BOOK-format filenames. Exact per-file SHA-256s, member completeness, original source fidelity and approval remain mandatory.

## 2026-11-16 — real native attestation draft completed

On [private full original and rebuilt SWORD CI #43867004627](https://github.com/icfmp/Bible-Resources/actions/runs/43867004627), the actual standard-compiler rebuild and libSWORD readbacks **PASSED**, including the six `BlockType=CHAPTER` `.cz*` members (no missing or extra native files), 24 previously vacant K aliases, 12 original K addresses changed only in the two source-corrected groups, all 1,255 original I and two TOP and four real Xiphos passage matches. The complete source audit was emitted into the existing time-limited, **metadata-only** GitHub Actions artifact, with no original commentary text or public ZIP.

- Pinned original native corpus digest: `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6`.
- Separate original-source **index-only recompile** native digest: `badb234e2c36543d8d5cb536ef8b722c31ccb02944177bc043a14e7b1eb0e045`.
- Current **two-correction private compiled** native digest: `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`.
- Exact metadata-only `SOURCE_AUDIT` draft SHA-256: `e51358a9b10185f2a45bbb63a38d6ccf063e8f492905f8519bf4ed9d54aaa7e4`.
- Exact compiled private ZIP (CI scratch only): `aeebadbc57d5a891d10ddb3dec520dcc8abd49e7cdd733c4a3542c77765282c4`.

The three corpus digests are **not interchangeable**: the original source bytes differ from the standard compiler's output. Native source/section semantic parity and the edited-source-versus-index-only exact compiled delta are separately checked. The attestation remains `private_draft_not_owner_authorized_for_release`; the production proof must be regenerated against the eventual **final versioned package**, including the owner-approved date and provenance config, before release. No owner authorization is inferred from a checksum.

## Decision implications in plain language

The original downloadable edition can be preserved exactly; the corrected
edition can be distributed later as a **new, traceable version**. Both still
use regular SWORD files; no new app-specific format and no Bible application
change are required. A corrected source can never be labelled as unchanged.
The cost is a separate, independently evidenced reconstruction audit for
such versions. The benefit is reliable corrections without losing the
source original or compromising the trustworthiness of the catalogue.

The delegated architecture choice is **not consent to license, release,
merge, upload, overwrite existing assets, or update public catalogue data**.
