# Upstream interoperability proposal — historical Segond 1910 reference identity

Status: evidence-backed proposal for CrossWire and eBible maintainers, **not an
approved transformation, release, or claim of existing reader compatibility**.
Date: 2026-11-08. Tracked in Bible Resources #12, PR #18, PR #23, PR #24.

## What we verified

- Original eBible `fraLSG` USFM and USFX archives independently contain the
  same 31,170 authored verse IDs across 66 books and 1,189 chapters, including
  `Mark.10.53` and ending Job 34 at verse 36.
- The 1910 printed edition's text transcription distinctly marks **Mark 10:53**
  and **Job 34:37**. Publisher eBible print output joins the content of the
  latter to verse 36. This suggests a source-digitization boundary discrepancy
  requiring publisher/facsimile confirmation, **not** license to edit USFM.
- The released CrossWire SWORD `Segond` registry ends Mark 10 at verse 52
  and includes a Job 34:37 slot. A complete, real `osis2mod -v Segond`
  / stock `diatheke` roundtrip classified exactly 1 authorial key appended
  to the preceding reader entry (`Mark.10.53` → `Mark.10.52`) and 1 empty
  registered key (`Job.34.37`). The continuous Bible characters survive
  after diagnosing display-only asterisks and whitespace; **reference identity
  does not**.
- All 18 released SWORD registries available in the pilot have been screened.
  None has the same numeric key set as the *current eBible* source.
  `Calvin` contains Mark 10:53 but introduces 22 source-only and 22 extra
  reader slots elsewhere. Simply switching registries is not a fix.
- A source-derived XML-v11n compiled under pinned SWORD development HEAD and
  exposed all 31,170 current authorial IDs, but stock SWORD 1.9 could not
  resolve Mark 10:53. It is an R&D result, not a portable module.

## Recommendation / upstream question

**Preferred scalable solution:** complete CrossWire's supported
module-embedded XML versification mechanism in a released SWORD C++ and
compatible JSword environment; include a stable published XML-v11n profile
or authorial-source-derived profile for this edition and test real frontends.
No application-specific workaround or private Bible binary.

CrossWire maintainers already confirm (2026-10-28/29) the XML-v11n mechanism
exists in SWORD HEAD, but explain that its use is not being promoted yet
because JSword compatibility remains to be implemented. See:
https://www.mail-archive.com/sword-devel@crosswire.org/msg37509.html

**Stable runtime fallback:** consider a separate, *versioned* official
`Segond1910` registry only if CrossWire considers it warranted, backed by
the 1910 facsimile's complete chapter/verse inventory. Do **not** silently
replace or enlarge the existing `Segond` table: previously compiled modules
depend on its immutable offsets (see CrossWire sword-devel, 2025-03-02:
https://lists.crosswire.org/pipermail/sword-devel/2025-March/050412.html).
Do not generate a one-off canonical override merely to pass our pilot.

Source audit **before proposing an exact registry**:
1. Inspect a photographed/page-scanned original 1910 printing for Mark 10:53
   and Job 34:37 and compare with eBible authoring data.
2. Report the Job 34:36–37 boundary evidence to the eBible source maintainer,
   ask for confirmation/correction in their maintained USFM/USFX and review
   full notes and poetry around that boundary. Don't patch upstream content
   silently in Bible Resources.
3. Rebuild *from any publisher-approved source revision*, preserving its
   immutable checksum and all editorial notes. Recompute the exact canonical
   reference set; for the historical edition, if the Job split is confirmed,
   the current eBible set of 31,170 keys will no longer be the appropriate
   accepted source baseline.
4. Verify that generated SWORD binaries carry independent addresses for
   every authorial verse, including Mark 10:53 and Job 34:37, on unmodified
   **released** engines. Then run full text, notes, reference targets, Strong,
   title, poem, original punctuation, and reader presentation checks.
5. Verify redistribution rights, reviewer sign-off and reproducibility.

## Explicit exclusions

- Do not silently join Mark 10:53 into 10:52 as a *published* solution.
- Do not conceal the reference loss behind a visual inline "53" string.
- Do not call an experimental SWORD HEAD XML-v11n module compatible with
  stock SWORD 1.9, JSword, Xiphos or all readers.
- Do not change published source verse keys merely to fit a compiler.
- Do not use a GenBook masquerading as a fully interoperable verse-indexed
  SWORD Bible: frontend navigation/parallel-study compatibility is not proven.
- Do not release, merge or close the pilot issues until a supported path
  actually passes the independent stable-runtime gates.

## Reproduction and references

- Stable real-corpus pilot:
  https://github.com/icfmp/Bible-Resources/actions/runs/42526118948
- Source/registy full comparison:
  https://github.com/icfmp/Bible-Resources/blob/test/lsg-segond-rebuild-roundtrip/docs/evidence/normalizer-3/lsg-sword-v11n-full-coverage.md
- Experimental SWORD HEAD:
  https://github.com/icfmp/Bible-Resources/actions/runs/42515854706
- CrossWire official av11n:
  https://wiki.crosswire.org/Alternate_Versification
- CrossWire exact importer behavior:
  https://wiki.crosswire.org/Osis2mod
- Printed 1910 transcription Mark:
  https://fr.wikisource.org/wiki/Bible_Segond_1910/%C3%89vangile_selon_Marc
- Printed 1910 transcription Job:
  https://fr.wikisource.org/wiki/Bible_Segond_1910/Job
- eBible Mark:
  https://ebible.org/study/content/texts/fraLSG/MK10.html
- eBible exact edition:
  https://ebible.org/fraLSG/copyright.htm

## Suggested request for upstream technical review (not sent)

Subject: Historical Segond 1910: Mark 10:53 reference loss in stable SWORD / XML-v11n rollout

We are rebuilding the public-domain Louis Segond 1910 from eBible's
maintained USFM/USFX. A 66-book/1,189-chapter full stock SWORD 1.9 trial
preserves the source character stream but `osis2mod -v Segond` silently
appends source Mark 10:53 to Mark 10:52 because the built-in Segond
registry stops at 52. The 1910 printed edition numbers 53 separately.
Separately, original Job 34:37 is numbered in the print edition while
eBible's source appears to join it with 36; we are asking eBible to review.

Would CrossWire recommend waiting for released module-embedded XML-v11n
with JSword compatibility, or adding a *new versioned* official Segond1910
registry (not changing the existing Segond offsets)? We can provide
fully reproducible text-free source-versification inventories, pinned
hashes and official compiler/reader diagnostics. Our requirement is
unchanged verse references and broad SWORD-client interoperability.

No upstream request has been sent by this document.
