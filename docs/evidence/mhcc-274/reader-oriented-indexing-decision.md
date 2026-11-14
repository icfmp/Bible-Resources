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
