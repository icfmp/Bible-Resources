# LSG 1910 eBible — complete SWORD versification coverage (research only)

Date: 2026-11-08. This document records numeric reference capacity only, not Bible text.
No candidate is approved or published.

## Source and method

- Real full-source GitHub Action: https://github.com/icfmp/Bible-Resources/actions/runs/42511512789
- Full PR: https://github.com/icfmp/Bible-Resources/pull/18
- eBible USFX ZIP SHA256: fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e
- eBible USFX XML SHA256: 90a53c3a61f0c07a329d8fc19c593b8c353f2b3e5a6830dbf4c53d2b08fd2141
- eBible USFM ZIP SHA256: 64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900
- Third-party converter pinned at adyeths/u2o SHA dde28bc545e8d8697fa5496c243187847ec55d31
- Built directly against the runner's installed CrossWire VersificationMgr using scripts/sword_v11n_ceilings.cpp. Source-v11n comparison: scripts/lsg_v11n_coverage.py. No Scripture text is emitted or stored.

Original edition: 66 books, 1,189 chapters and 31,170 authored verse identifiers.

## All 18 registries

Outside: original publisher IDs which cannot be represented as numerical verse slots in the registry.
Unoccupied: numerical registry slots in an original source chapter without a matching source ID. These can be editorially omitted verses, blanks, or mismatched numbering. The audit never fills them.

| Registry | Source IDs outside | Registry slots unoccupied |
|---|---:|---:|
| Segond | 1 | 1 |
| Calvin | 22 | 22 |
| DarbyFr | 84 | 21 |
| German | 109 | 90 |
| Luther | 109 | 90 |
| Catholic | 109 | 176 |
| Catholic2 | 109 | 186 |
| NRSV | 112 | 46 |
| NRSVA | 112 | 46 |
| KJV | 114 | 46 |
| KJVA | 114 | 46 |
| LXX | 807 | 1508 |
| Orthodox | 807 | 1508 |
| SynodalProt | 833 | 826 |
| Synodal | 833 | 900 |
| Vulg | 845 | 912 |
| Leningrad | 8067 | 89 |
| MT | 8067 | 89 |

There is NO exact original source slot set among the 18 built-in registries.
The absence of a source ID may represent a genuine editorial absence; no synthetic verse or annotation is licensed by this numeric test.
Registry capacity is not a substitute for a full compiler and reader round-trip.

## Confirmed real verse-boundary failures

The complete 1,189-chapter SWORD readback:
https://github.com/icfmp/Bible-Resources/actions/runs/42490352755

The built-in Segond system folds source Mark 10:53 into reader Mark 10:52 (the combined non-whitespace Scripture character stream is verified) and exposes an EMPTY Job 34:37 reader slot. Both reference mappings are unacceptable even though the words are preserved. The publisher includes Mark 10:53 in this source edition:
https://ebible.org/study/content/texts/fraLSG/MK10.html

The original shipped SWORD module advertises NRSV, but the published edition's source IDs have 112 out-of-NRSV slots. A module's advertised metadata is not evidence of source fidelity.

## Potential standards-based next steps, NOT yet selected

1. SWORD development HEAD may provide XML-defined dynamic versification. Maintainer Troy A. Griffitts explicitly stated on 2026-10-28/29 that extensible XML v11n is implemented in HEAD, but JSword compatibility has not been promoted:
   https://www.mail-archive.com/sword-devel%40crosswire.org/msg37509.html
   Claimed upstream docs:
   https://git.crosswire.org/main/sword/-/blob/master/doc/v11n-xml.md
   Verify the actual file format, stable-version availability, module packaging, SWORD C++ and JSword frontend compatibility and GNOME app's Python/libsword usage before proposing an upgrade.
2. If mature XML v11n is not deployable, discuss an edition-specific versification with CrossWire upstream, derived *generically* from immutable authoring source metadata and independently reviewed. It would likely depend on a new SWORD runtime and could be rejected upstream. Do not hand-code just Mark and Job.
3. Defer publication. Keep publisher USFM/USFX and candidate OSIS only in their audited, nonpublic form.

Official SWORD documentation explains that out-of-range verses are appended to previous canonical slots rather than preserved as separate indexed entries:
https://wiki.crosswire.org/Alternate_Versification

No decision to change the reader library, use a nonstandard binary, publish this edition, or silently renumber/edit the Bible is made here. PR #18 and issues #3/#12 remain open pending architecture/editorial approval and all remaining integrity gates.
