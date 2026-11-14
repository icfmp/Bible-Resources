# MHCC — reader-oriented commentary indexing decision

**Date:** 2026-11-14  
**Track:** [editorial audit #274](https://github.com/icfmp/Bible-Resources/issues/274), [draft audit PR #275](https://github.com/icfmp/Bible-Resources/pull/275).  
**Decision source:** project owner explicitly prioritizes a better reader experience over reproducing an upstream CrossWire indexing choice.  
**Status:** editorial/navigation direction approved; exact per-entry mappings, candidate build, reader QA, rights and publication are **not** yet approved.

## Principle

A Bible commentary *section* remains a single authorial unit, whether it discusses:
- one verse;
- a continuous passage;
- discontinuous passages (e.g. Matthew 13:24–30 **and** 36–43, never 24–43);
- or one chapter as a whole, with no assertion that the author comments on each verse individually.

**Reader objective:** when the user studies any verse belonging to the verified scope of a section, the corresponding comment must be discoverable. When reading a chapter or selected passage, a linked comment should normally appear **once**, under a truthful passage/chapter heading rather than repeated under every verse. Original authorial wording and internal quotes are untouched.

Being identical to CrossWire MHCC 2.0 is a **provenance guarantee**, not an instruction to keep inferior verse-level navigation in our separately curated edition. CrossWire's own standard OSIS commentary `annotateRef` supports continuous and discontinuous ranges; `osis2mod` supports native linked verse entries. We must exploit those *standards*, not create proprietary annotation data:

- https://wiki.crosswire.org/OSIS_Commentaries
- https://wiki.crosswire.org/Osis2mod

## Mandatory separation of concerns

1. **Immutable upstream witness:** keep exactly pinned CrossWire bytes and BRMHCC 0.1.0 unchanged and available for comparison.
2. **Authored editorial section extent:** based on the chapter division, original heading, corresponding commentary body, and independently examined edition witnesses; a scripture cross-reference alone **cannot** declare commentary scope.
3. **Proposed target verse set:** machine-readable list of eligible canonical verse keys. A chapter-scope comment may link to every verse of that chapter *only after its chapter scope is proven*; the label must continue to say **chapter commentary**, not that the author wrote a distinct interpretation of each individual verse.
4. **Linked native representation:** link those keys to the *one* unchanged original authorial body rather than copying it into multiple independent texts. If SWORD/reader cannot do this faithfully, block that candidate and investigate the standards-supported alternative.
5. **Deduplicated presentation:** a viewer offering a whole chapter must not display the same commentary 43 times because 43 keys point to one authorial section. Verify actual behavior in Bible and at least one independent reader.
6. **Evidence and rollback:** each transformation has exact source digest, original module identity, old mapping, proposed added keys, identical-content check, coverage class, rights/edition gate and reversal procedure. Zero silent corrections.

## Existing findings and intended treatment

| Original stock behavior | Proposed best reader behavior | Editorial qualification |
| --- | --- | --- |
| 16 comma-separated two-verse sections whose second key is absent | Link the absent second key to the original section | Verify each passage's actual extent; keep punctuation and prose unchanged |
| Matthew 13:24–30 and 36–43 is linked only at 24–30 | Link 36–43 to the same section | Preserve the separate Matthew 13:31–35 comment; **never** fill the gap |
| 118 chapters with one occupied key (verse 1) | Make a verified whole-chapter commentary accessible from every verse, display once per chapter | These are **118 review candidates**, not 118 proven errors; check each original section before proposing links |
| Amos 1 has the same whole-chapter entry at all 15 native verses | Preserve existing links and deduplicate in chapter displays | No need to rewrite or reinsert already indexed keys |
| Titles mentioning verses but missing a numeric range (Psalms 16, 70) | Preserve title and continue provenance-based review | No invented reference from a vague title |

## Fail-closed algorithm requirements

- Derive the target keys only from explicit, reviewed section scopes; never from a titleless verse-1 anchor or `scripRef` alone.
- Validate book/chapter/verse with the module's actual versification registry, including chapter max, verse max and any legitimate canonical omissions; do not infer missing Bible verses.
- Preserve discontinuous ranges as disjoint sets.
- Reject any plan where a target is occupied by a **different** original commentary payload. Existing same-payload keys are verified no-ops, not reinsertions.
- Reject mixed or conflicting source testimony, nonunique/missing source master keys, unverified duplicate shares or overlaps, and scope claims crossing into other independently authored sections.
- Ensure a full section/body reference audit before and after rebuild: all original keys/intros/TOP preserved in canonical order with original raw payload fingerprints; modified or added link keys exactly enumerated; no original authorial XML, citations or paragraphs rewritten.
- Record status as **PROPOSED**, **BLOCKED** or **EDITORIALLY_APPROVED**, never as a verified editorial correction solely because CI passes.

## Implementation and approval gates

The independent diagnosis remains in PR #275. Prepare a generic read-only **link-plan validator** as the next step. After section-level editorial evidence and rights are checked, build an isolated SWORD candidate from reviewed standard commentary OSIS, run complete source-to-module parity and link readback, then test that chapter reading deduplicates commentary. Prefer an upstream CrossWire report where an actual upstream source/converter bug is confirmed.

**Approval boundary:** project owner has authorized pursuing reader-first indexing even if it differs from CrossWire's design. This **does not** imply permission to change the published BRMHCC 0.1.0, release a revised module, or restart paused modern-English edition #270/#272.


## Native index mutation feasibility — verified 2026-11-14

The standard `osis2mod` route is experimentally supported: a synthetic,
invented-content OSIS commentary compiled as `zCom` was read back by an
independent stock libSWORD reader, proving that contiguous and disjoint
`annotateRef` sections work and do not absorb another section in the gap.
Evidence: [synthetic OSIS run #43622505845](https://github.com/icfmp/Bible-Resources/actions/runs/43622505845).

The simpler **in-place compiled-index link** idea has a concrete limitation:
the released libSWORD 1.9 zCom loaded through `SWMgr` is **read-only**.
On an entirely invented synthetic module copy, the supported `isWritable()`
check returned false, so public `linkEntry` could not be used safely.
An explicit capability-gated test confirmed the original synthetic module's
11 occupied native entries and all its compressed `.czz` records were
unchanged. Evidence: [capability test #43623537818](https://github.com/icfmp/Bible-Resources/actions/runs/43623537818).
Do **not** change raw `.czv/.czs` index bytes outside a documented SWORD
writer or attempt a bypass of the read-only guard.

Therefore the next candidate must use an **officially supported writer or
a newly compiled, separately identified, reviewed OSIS source**, followed
by strict full original/proposed content, markup, introductions, notes,
references and native-verse readback parity. Replacing the original
CrossWire compressed corpus with unverified CCEL text is not allowed.
A new compiled module with same words is not by itself proof of equal
authorial edition or preserved original markup.

This is a technical route decision, **not** editorial approval or permission
to publish. The 17/24 explicit section-index anomalies and 118 whole-chapter
reader-navigation proposals still require their own reviewed scopes,
unchanged original provenance, deduplicated reader UX and separate release
approval.


## Private whole-corpus 24-target index preview — validated technical behavior (2026-11-14)

The direct `SWMgr` / public `zCom::linkEntry` approach remains blocked
by the released module's read-only driver. Binary `.czv` index patching would
bypass the supported API and risks a hidden source/index mismatch. Therefore
**prefer one standard, source-constrained `osis2mod` rebuild only when
an actual new corrected SWORD module is justified**. Do not present this as
changing the historical CrossWire stock in place.

The generic `build_complete_original_transport` now optionally consumes
**strictly bounded, provisional same-chapter aliases**. Each new key must
be vacant in the exact original K map and name an existing original master
with matching SHA-256; grouping merges adjacent references but NEVER joins
across an independent original section or a discontinuous gap. The *single*
original source raw body is included once in the OSIS section with multiple
standard `annotateRef` ranges. Bad hashes, cross-chapter aliases and
occupied target attempts fail closed in synthetic regressions.

[Exact pinned original private audit #43645508238](https://github.com/icfmp/Bible-Resources/actions/runs/43645508238)
**SUCCESS**. This experimental preview has **17 original heading-derived
candidate sections / 24 unoccupied canonical proposed keys**. Actual
`osis2mod` + independent native libSWORD readback established:

| Verification | Original unchanged | Provisional preview |
| --- | ---: | ---: |
| Original K slots retained | 28,718 | **28,718/28,718** |
| Original I slots retained | 1,255 | **1,255/1,255** |
| Original TOP slots, exact raw payload | 2 | **2/2** |
| New native K aliases | 0 | **24**, exactly the proposed keys |
| Original K/I missing or overwritten | 0 | **0** |
| Additional unexpected K/I | 0 | **0** |
| New alias native raw content equal to its compiled original master | n/a | **24/24** |

Every original K/I entry also passes the existing complete
word-order, whitespace-normalized original visible punctuation/text,
non-`div` element/attribute, original `div` attribute and ordered
`reference` target invariants. Compiler-added `div` wrappers mean this is
**not exact original XML byte equality** or a reader-layout certificate.

**Critical editorial boundary:** these particular 17 scopes come from a
*heading-based original source diagnostic*, not 17 signed-off authorial
section decisions. The source-independent CCEL `scripRef` witness
corroborates citation ranges but does not itself establish `scripCom`
commentary anchors. Therefore the preview is deliberately labelled
`source_scope_editorially_approved=false`, not published, and **must not**
be used as an approved corrected release recipe yet. The separate 118
chapter-first candidates, Lev 19/Ps 108 intro-only bodies, cross-witness
annotation differences and one wording variant are untouched.

**Next decision gates:** individually review the 17 boundaries and 24
targets from the actual authorial commentary, original chapter outlines
and independent editions; verify truthful contiguous/discontinuous
section headings; exercise the preview in Xiphos on actual affected
passages, including deduplication and independent intermediate
commentary. Only then propose a separately versioned corrected module
for owner publication approval. BRMHCC 0.1.0 remains byte-immutable,
and modern-English #270/#272 stays paused.


## Authentic independent Xiphos preview — targeted passage navigation verified (2026-11-15)

[Exact pinned-original private CI #43652204356](https://github.com/icfmp/Bible-Resources/actions/runs/43652204356)
**SUCCESS**, including synthetic negative tests, the complete 29,975 original
K/I/TOP corpus comparison, and 24/24 exact provisional additional SWORD
verse-index aliases. The same runner installed a SHA-attested real published
`BRLSG1910` Bible alongside the **temporary** corrected `BRIndexProbe`
zCom, started the **actual independent Xiphos GTK program** in an isolated
X11 session, selected proposed alias verses, and compared text copied from
the actual commentary pane against the independent `diatheke` readback.

| Actual proposed alias selected | `diatheke` alias/master shares ≥25 consecutive original words | Xiphos GTK passage accepted and actual commentary copied |
| --- | --- | --- |
| `Eccl.4.8` | Yes | **Yes** |
| `Isa.21.12` | Yes | **Yes** |
| `Matt.13.36` | Yes | **Yes** |
| **Total** | **3/3** | **3/3** |

Selection is source-neutral in the script: it chooses the largest original
multi-verse alias group and representative aliases from other books; these
are the resulting original MHCC cases, not hardcoded exceptions.

This is **genuine reader use**, not merely a visible Xiphos window. The
original commentary and biblical text are never uploaded to reports;
screenshot pixels never leave the temporary X11 runner. The linked
commentary content remains one original authorial raw section, not copied
into 24 authored expositions.

**Boundary:** this proves actual selected-verse retrieval on three real
target keys, **not** full 24/24 visual passage QA, perfect paragraph layout,
correct cross-reference click-through, or deduplication when a *whole
chapter* is rendered as multiple verse keys. The complete native and
`diatheke` indexed-payload gates cover all 24; whole-chapter reader
deduplication is still a separate concern and must not be asserted as
passed. Neither the published `BRMHCC` package nor the original CrossWire
text was edited. Source scope/edition approval and publication remain held.


## Important reader regression: chapter-wide `diatheke` repeats real linked entries (2026-11-15)

The native **24/24 new indexed-key parity result is valid**, but **must not
be mistaken for satisfactory entire-chapter display**. [Private original
versus preview CLI chapter comparison #43653681714](https://github.com/icfmp/Bible-Resources/actions/runs/43653681714)
**SUCCESS** on the real CrossWire MHCC and the temporary `BRIndexProbe`
candidate. Four independent, exact 20-word original commentary windows per
master section were counted in a full-chapter `diatheke -f plain` rendering
of *both* original and proposed modules. Every source window was unique in
its original entry. No source words left the ephemeral runner.

| Real chapter | Original exact original-section excerpt occurrences | With provisional verse aliases |
| --- | ---: | ---: |
| Matthew 13 | 7 | **15** |
| Isaiah 58 | 1 | **2** |
| Jeremiah 4 | 1 | **2** |
| Ecclesiastes 4 | 1 | **2** |

This is **not original text duplication in the zCom source**: native linked
keys share one identical original authorial payload. It is a **reader
presentation** effect of iterating verse keys without grouping linked
entries. It already affects **existing CrossWire range-linked commentary**,
as shown by the baseline seven occurrences in Matthew 13.

**Editorial/architecture consequence:**
- Do not silently remove correct passage aliases solely to make an
  unsophisticated full-chapter renderer print each unit once.
- Do not automatically add thousands of whole-chapter links among the 118
  first-verse-only cases. Their origin and purpose must first be individually
  classified; a full-chapter reader could show dozens of repeated copies.
- Build chapter/selection display from **independent authored sections**
  with shared native link identity and contiguous/discontinuous passage
  scopes, not by naïvely rendering every occupied verse key as a new
  commentary section. A correct presentation must keep separate
  independently authored adjacent sections distinct.
- Do not equate `diatheke` output with Xiphos GUI, Bible's renderer, or
  any other reader. A bounded real GUI check is required before asserting
  which clients are affected.

The proof establishes a reproducible concrete **UI regression risk**,
not a failure of content preservation or new authorial index scope.
The separate source release and editorial hold continues.
