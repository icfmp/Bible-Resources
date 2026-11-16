# MHCC — renewed edition-first editorial sweep (2026-11-16)

**Scope:** the authored/edited work is the editorial reference, not
CrossWire's SWORD serialization. CrossWire `MHCC 2.0` is the immutable
digital transmission witness to inspect and improve where justified.
The separate CCEL ThML witness is an *independent digital comparison*, not
an authenticated copy of the same historical print edition or a source of
markup that Bible Resources may copy automatically.

**Track:** [editorial investigation #274](https://github.com/icfmp/Bible-Resources/issues/274) ·
[draft PR #275](https://github.com/icfmp/Bible-Resources/pull/275) ·
[release gate #276](https://github.com/icfmp/Bible-Resources/issues/276).

## Exact evidence retained

- Pinned CrossWire `MHCC 2.0` original ZIP SHA-256:
  `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d`.
- Pinned, comparison-only CCEL ThML SHA-256:
  `4a5509ba5064b54572397ae1a796561ff6ce4a1e18f366af0141a09c5d06fcd6`.
- [Complete new native/layout/source SWORD audit #43786426189](https://github.com/icfmp/Bible-Resources/actions/runs/43786426189)
  **SUCCESS**: all 28,718 original numbered K, 1,255 I and two TOP
  reconciled. The separately compiled **private** BRMHCC 0.1.1 still differs
  only in 11 original K addresses linked to one narrowly edited Ezekiel
  citation/label; all other original K/I/TOP/native source linked boundaries
  remain intact; real Xiphos three-passage tests pass.
- The original `BRMHCC 0.1.0`, catalogue and all pinned original source bytes
  have **not** been changed. The modern-English modernization remains paused.

## Previously unresolved editorial cases revisited

| Case | Existing independent evidence | Edition-first decision for 0.1.1 |
| --- | --- | --- |
| 16 source-heading two-verse coverage gaps | Original explicit heading, genuinely absent secondary native K address, matching CCEL leading exposition and 20-word overlap for all 16 | **Retain the 16 reviewed alias corrections**; authorial prose untouched |
| Matthew 13:24–30 **and** 36–43 | Original disjoint heading, separate original 31–35 section, independently observed displayed grouping | **Retain the 8 reviewed aliases only**; never bridge 31–35 |
| 118 original one-key-at-verse-1 chapters | **116** independently corroborated undivided source divisions; **2** atypical chapters (`2Chr.1` and `Neh.1`) whose content/book-prefix/title is accounted for without proven lost authorial prose | **Do not automatically add 2,285 more K aliases.** Full-chapter discoverability is a worthwhile separate reader-experience improvement, but linked entries demonstrably repeat in chapter-wide `diatheke` renderings. Scope must be represented truthfully once per authored section |
| `Lev.19` / `Ps.108` | Source commentary prose is present in original **I chapter introductions** and not missing; no native numbered K keys | **Keep the I-owned content**, do not move it or misrepresent it as individual verse commentary; consider a separately reviewed chapter-accessibility strategy |
| 25 CCEL-vs-CrossWire link-target differences in 20 one-key chapters | **18** source labels remain ordinary CrossWire prose, **1** is already linked to a different target, **3** have punctuation/markup differences, **3** are not present at the selected stock position; **14** of the plain-text labels have one unambiguous occurrence | **No automatic CCEL annotation copying or retargeting.** A fresh hypertext enhancement may be researched from independently verified *existing CrossWire literal labels*, canonical verse identity and rights, not assumed from CCEL's digital links; this is not evidence of missing authorial commentary |
| Ezekiel 3 reversed chapter-summary citation | One actual source-body `reference/@osisRef` and visible `3:12–2` label; the separately indexed original commentary and distinct digital witness corroborate `3:12–21` | Exactly one byte-reversible label+target correction is **privately compiled and verified**, not approved for public redistribution |

## New independent full-layout census: what it really proves

The new reusable `scripts/commentary_layout_census.py` inspects all original
native I/K/TOP entries with safe XML parsing, deduplicates exact linked raw
bodies, and emits only counts and bounded original native-key addresses.
It makes **no editorial or authorial verdict**.

[Complete first census and independently refined rerun](https://github.com/icfmp/Bible-Resources/actions/runs/43786426189):

- **5,302** distinct raw original commentary/introduction bodies: **4,047 K**
  and **1,255 I**; **24,671** additional raw aliases. Canonical original
  K/I/TOP counts still match the whole native inventory.
- All **4,047** distinct K raw bodies have **at least two `div` nodes**,
  despite **zero** literal `p` and `l` nodes in their native SWORD XML.
  Accordingly, the absence of `p` is **not evidence of lost paragraphs**:
  these texts are structurally represented through other markup.
- **792** distinct K bodies contain `table` structures; **3,928** have
  highlighting `hi` elements. All **2,860** detected visible numbered
  verse leads at the start of a K body are already styled as such by
  a corresponding initial `hi` element. They are **not** automatically
  defective or absent headings because no `title` node is used.
- All **118** native verse-1-only chapter K bodies likewise have no literal
  `p`, but are included in the all-K `div` evidence above.
- Word-size bands (K distinct bodies): **971** with 1–99,
  **2,202** with 100–249, **808** with 250–499 and **66** with 500+
  per-original-XML-fragment word tokens. These are estimates for
  readability triage, **not** a normalized Scripture/text-length claim.
- With `div` and table separation and styled `hi` headings properly
  accounted for, the **conservative automatic layout review-candidate
  categories are empty**. A prior, invalid “no `p` means no structure”
  heuristic would have produced hundreds of false positives; it has been
  replaced and tested using invented paragraph-div, table and styled-title
  fixtures.

**Limits:** This is a **structural-presence result**, not a full comparison of
paragraph *boundaries* with the named historical edition, actual GUI
pagination, typography or an assessment of every long authored passage. Two
or more `div` tags are not proof that each is a correctly positioned
paragraph; no unreviewed markup transformation is authorized from this
census. A later visual/edition-aligned check can focus on long originals
(e.g. John 3, Exodus 12, Matthew 4), but must first establish whether
actual reader display or source paragraph boundaries are wrong.

## Outcome and publication boundary

**No additional content correction is justified by this sweep.** The existing
17-section / 24-key navigation plan and narrowly documented Ezekiel 3
correction remain the only technically tested changes for a private
`BRMHCC 0.1.1`. The 118 chapter-wide navigation question, 25
cross-edition annotation differences and source paragraph-to-digital-layout
equivalence remain *different review tracks*, not reasons to rewrite or
silently supplement authorial content.

No historical print copy has been authenticated; no claim of exact Matthew
Henry/abridger paragraph intent is made. Any new edition-enhancing
decision must be mapped to exact source witnesses, independently checked,
reversible or reproducible, legally distributable and expressly approved.
The normal release path still needs a distinct attested **rebuilt-commentary**
validator, independent code review and the owner's separate publication
authorization. Codex must **not** be invoked without advance permission.
