# MHC 2.2 — recover authentic dual commentary scopes without repeating source prose

> **Superseded navigation checkpoint — 2026-11-19.** This document retains the
> original experimental **7 → 2** multi-owner retrieval evidence for audit
> reproducibility. It is **not** the final first-candidate navigation policy.
> The owner subsequently approved whole-verse indexing **Romans 4:9–16 /
> 4:17–22**, preserving both complete authored word streams but deliberately
> not providing two verse-17 owner entries. The remaining distinct
> **2 Chronicles 1 preface** has been moved into a genuine OSIS chapter
> introduction (SWORD `2Chr.1.0`), with the separate 1:1–12 commentary
> retained. The real private source→SWORD recompilation and native readback
> [#44346559230](https://github.com/icfmp/Bible-Resources/actions/runs/44346559230)
> passed this introduction classification without changing source prose,
> punctuation, notes or references. Thus the corrected first candidate
> does **not** require a reader-side proprietary dual-commentary sidecar.
> The `1` remaining reader multiowner key in the intermediate
> `mhc-shared-scope-review-private.json` plan is **pre-introduction-stage**
> metadata, not the final compiled navigation result. No GUI or publication
> acceptance is inferred. See the
> [updated first-candidate decision record](mhc-first-candidate-decisions-2026-11-18.md).


**Status (2026-11-18): private technical prototype on draft
[PR #286](https://github.com/icfmp/Bible-Resources/pull/286), not
a published index or a reader feature.**
Track the [parent issue #285](https://github.com/icfmp/Bible-Resources/issues/285).
The unchanged official MHC authoring OSIS is pinned to Git
`537591a94c991941877b47a06666b6a7812e05d8` and SHA-256
`3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`.

## Two different kinds of original overlap

The authoring source had **seven** shared verse keys involving **14**
independent authored sections. These are syntactic source assignments,
not seven independently established substantive sub-verse divisions.

Independent [complete Henry section indexing](https://www.biblegateway.com/resources/matthew-henry/Romans)
and the reviewed private source-attribute plan show that five are
machine-scope indexing mistakes, already represented by a disjoint KJV
verse boundary in the corrected SWORD:

| Previously shared source key | Private corrected whole-verse boundary |
| --- | --- |
| `Ps.95.7` | preceding section 1–6; following section 7–11 |
| `Rom.7.14` | preceding section 7–13; following section 14–25 |
| `2Thess.2.3` | preceding section 1–2; following section 3–12 |
| `2Pet.2.3` | preceding section 1–2; following section 3–6 |
| `Rev.4.8` | preceding section 1–7; following section 8–11 |

**Do not use the raw seven-overlap inventory as a reader-side directive
to display two authored sections on each of these five corrected keys.**
This would reintroduce wrong navigation.

Only two cases legitimately need multi-section reader treatment in
this first source-specific candidate:

| Verse | Original sections / navigation | What is preserved | Still needed in UI |
| --- | --- | --- | --- |
| `Rom.4.17` | Independent authorial scopes **9–17a / 17b–22**. Retrieve native first-key commentary entries `Rom.4.9` and `Rom.4.17` in source order | Both original full authorial word streams, without repeating or deleting source content in zCom4 | Show two distinct sections when verse 17 is selected; deduplicate group identity while navigating |
| `2Chr.1.1` | Both original `2Chr.1.1` and `2Chr.1.1-12` sections use one real SWORD key `2Chr.1.1` | Both complete bodies are found inside that compiled entry | Check their independent section/heading markup rather than assuming one XML raw body equals one original authored section |

## Implemented source-neutral approach

The generic, **private, metadata-only** functions
`source_commentary_shared_key_retrieval_map` and
`source_commentary_reviewed_shared_key_plan` in
[`scripts/audit_osis.py`](../../../scripts/audit_osis.py):

1. Enumerate actual original commentary OSIS verse-group source identities
   with distinct SHA fingerprints (source line, original scope, full body).
2. Verify that every original source group's first referenced native key
   is genuinely occupied in the independently read compiled SWORD index.
3. Keep source-order native retrieval keys, including sections with the
   same first native key, **without exporting original prose**.
4. Compare the untrimmed original source's overlaps with the separately
   corrected, compiled-candidate source's overlaps.
5. Retain a corrected-away original overlap only under a separately
   source-SHA-pinned and **independently evidenced** private editorial
   exception; currently only the original Romans 4:17a/17b split.
6. Materialize the tiny resulting navigation map **only in the private
   CI runner temporary directory**, with no source paragraphs, notes,
   copyrighted text, repository resource file or public artifact.

The private [review plan](../../../config/commentary-osis-repair-plans/mhc-shared-scope-review-private.json)
records the Romans 4:17 independent section-index witness and checks
the exact expected 7 original → 1 corrected-source + 1 retained
intra-verse exception → **2 actual reader multiowner keys** transition.
Nothing in the generic code is keyed to Matthew Henry, English wording,
Romans, or a provider. Its synthetic tests use French accents, Greek
Unicode and source-identical / invalid-index cases.

**First actual source/native bridge proof:** [CI #44328992969](https://github.com/icfmp/Bible-Resources/actions/runs/44328992969)
PASS; 4,256 original authored groups, seven original overlapping keys,
14 involved sections, independently verified native retrieval
`Rom.4.9` + `Rom.4.17` and same-key `2Chr.1.1`.
**Final edited-source versus actual compiled SWORD validation PASSED:**
[real private full MHC Actions run #44331003046](https://github.com/icfmp/Bible-Resources/actions/runs/44331003046).
The actual pinned source/native run reported:

- Original source: **4,256** authored section groups, **7** original
  syntactic overlapping verse addresses and **14** participating sections.
- Independently reviewed machine-boundary errors: exactly **5**
  original shared-verse addresses **not** carried into the reader plan.
- Real double-owner keys still required: exactly **2**, with
  `Rom.4.9` + `Rom.4.17` as two distinct native retrieval keys and
  `2Chr.1.1` as one native key containing two separate source bodies.
- All **4,256** original source group word streams verified present at
  their actual native first keys; the separately recompiled **25**
  reference-only changes and all **32,355** occupied SWORD keys remain
  valid. **Zero** source prose exported by the navigation map.
- A deterministic, versioned, metadata-only JSON proof was serialized
  and independently re-read inside `RUNNER_TEMP`, with **no uploaded
  artifact, public catalogue item or published sidecar**.

This is an actual private source-to-compiled native retrieval result,
not merely a proposed grouping or a GUI test.

## Acceptance boundary and next implementation owner

This is a **faithful retrieval-index proof**, not an automatically
released sidecar format, a modified OSIS commentary, or proof that a
SWORD GUI can display two separate sections simultaneously.
The existing standard SWORD zCom4 remains the only commentary content
transport; the source-derived lookup does not duplicate text.
Actual Bible UI consumption of the two multi-owner keys is a separate
architectural/release decision requiring user approval, tests, and an
explicit policy for distinguishing inner authored sections at the
same native `2Chr.1.1` key. Do **not** add a one-off Romans code branch,
invent subverse SWORD addresses, or make a new proprietary commentary
prose format.

CrossWire/CCEL edition and electronic rights, real clicked references
and final release/owner approval remain independently open.
