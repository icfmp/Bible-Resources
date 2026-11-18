# MHC — remaining 23 machine Scripture-link review anchors (2026-11-18)

**Research inventory, not a corrected edition, module release, or editorial approval.**
This is the original **complete MHC** authored OSIS, *not MHCC*. The original
source at CrossWire Git revision `537591a94c991941877b47a06666b6a7812e05d8`
and SHA-256 `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`
is unchanged. Original XML line numbers below refer to that exact source.

The [actual pinned source examination (GitHub Actions #44292726273)](https://github.com/icfmp/Bible-Resources/actions/runs/44292726273)
reported **25** nonstandard `reference/@osisRef` source values, with their
original machine locators, enclosing book and visible citation-label SHA.
The separate [private two-link correction preview](https://github.com/icfmp/Bible-Resources/actions/runs/44291942651)
safely trialled **line 7237** (`15.1` → `Jer.15.1`) and
**line 57059** (`Ezr 1.7 8.23` → `Ezra.1.7 Ezra.8.24`), leaving
authorial visible labels and prose untouched. Neither is published.
The remaining **23** anchors are listed below, without commentary prose.

## Five bookless numeric machine targets

| Original line | Enclosing source book | Original `osisRef` | Exact short displayed citation | Triage, not approval |
| ---: | --- | --- | --- | --- |
| 3108 | Gen | `21.13` | `xxi. 13` | `Gen.21.13` is a *candidate only*; check actual host prose/citation first |
| 32130 | Job | `18.24` | `xviii. 24` | **Cannot** infer `Job.18.24`: that KJV verse does not exist; inspect which book is cited |
| 37835 | Ps | `10.1-4` | `x. 1-4` | `Ps.10.1-Ps.10.4` is a *candidate*; keep the entire range |
| 41584 | Ps | `4.4` | `iv. 4` | `Ps.4.4` is a *candidate*; independently verify target book |
| 47698 | Prov | `5.7` | `v. 7` | `Prov.5.7` is a *candidate*; independently verify target book |

The source book and citation alone are not independent proof of the cited
Bible book. No numeric target has been silently prefixed or edited.

## Eighteen compound / inherited-context machine targets

These forms may encode several **independent** destinations, inherited
chapters or verses, or a whole range. Whitespace tokenization alone can
change the intended references. Exact machine syntax is retained here so
source-bound review can be resumed without rereading full logs.

| Original line | Enclosing book | Unchanged source `osisRef` |
| ---: | --- | --- |
| 50767 | Prov | `Pr.10.19 11.12 12.23 13.3 17.27 28 29.11 20` |
| 50772 | Prov | `Pr.11.14 15.22 18.13 19.2 20.5 18 21.29 22.3 25.8-10` |
| 50794 | Prov | `Pr.16.3 18.10 23.26 27.1 28.25 29.25` |
| 50803 | Prov | `Pr.17.17 18.24 27.9 10 14 17` |
| 52749 | Isa | `2Ki 2.3 4.1 38 5.22 6.1` |
| 58059 | Isa | `Ps 60.1 2Sa 8.13 14` |
| 58803 | Jer | `De 4.29 30.2` |
| 62922 | Ezek | `La 4.3 4 5.10` |
| 63871 | Ezek | `Le 18.19 20.18` |
| 67688 | Hos | `Ho 4.15 12.11 Am 4.4 5.5` |
| 76239 | Matt | `1Ti.4.1 2Ti 3.1 2 3.3` |
| 81529 | Matt | `Lu.24.6 7-44 Mk 16.7` |
| 95558 | John | `1Jo.1.1 2Pe 1.16` |
| 97929 | Acts | `Ac.23.23 24 25.6` |
| 98022 | Acts | `De.7.7 8 9.5 6 Mt 20.10` |
| 98544 | Acts | `Heb.9.9 10.1 4` |
| 109003 | Phlm | `Col.3.1 2Pe 2.4` |
| 112877 | Jude | `1Ti.4.1 2Ti 3.1 2Pe 3.3` |

## Next bounded technical gate

1. For **each individual** original link, inspect the exact visible citation
   (including cases omitted from public diagnostic output because the short
   source label exceeded its strict length limit), host context and any
   independent printed/digital witness. Preserve the visible label.
2. Expand only proven references to explicit book/chapter/verse destinations.
   Preserve every separately intended target and any full verse range;
   check each against the real independent KJV SWORD verse registry.
3. Add verified edits, if any, as individually reversible SHA/line/label-bound
   private plan entries using existing
   `patch_reviewed_osis_reference_attributes`; do not write a new importer,
   infer a book from the host, or split composite references on spaces.
4. Recompile privately and compare full first-key body, note and reference
   metadata; test actual hyperlink navigation in Xiphos and AndBible.
   GUI startup or retained raw attributes are **not** click-navigation proof.

None of the 23 links is asserted repaired, and none of these hypotheses
authorizes changes to historical wording, punctuation, section ownership,
copyright status, public OSIS, or published SWORD.
