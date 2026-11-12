# Draft publisher report: BPC J. N. Darby 2024 revision 2.0 OSIS note links

**DRAFT FOR REVIEW — NOT SENT TO BPC.** This file is an upstream-facing
diagnostic packet, not a source patch, publisher acknowledgement, or
authorization to change a published Bible. Any eventual correction must be
obtained from BPC or explicitly approved as a separately documented
derivative. The current research SWORD data and original OSIS attributes
remain unchanged.

## Edition and reproducibility

- Publisher: Bibles et Publications Chrétiennes (BPC).
- Edition: French J. N. Darby, **2024 revision 2.0** (not the separately
  distributed later *Darby révisée*).
- Original: https://cdn.editeurbpc.com/bible/osis/JND/bible_jnd_2_0.xml
- Exact original XML SHA-256:
  `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`.
- Publisher's own [error-report form](https://editeurbpc.com/signaler).
- Read-only source/native evidence: [BPC OSIS audit](https://github.com/icfmp/Bible-Resources/actions/runs/43089960679),
  [independent source/native equality audit](https://github.com/icfmp/Bible-Resources/actions/runs/43014891638),
  [case-by-case technical record](frajnd-2024-stage5-editorial-review.md).
  These are GitHub Actions runs, not publisher decisions.

## Clarification/correction candidates for the publisher

The table contains **original `osisRef` XML attribute values**, not a
requested rewriting of the displayed notes. The proposed values are
*contextual hypotheses*; please check against the publisher's editorial
intent and authoritative source before changing anything.

| Note host | Original `osisRef` | Suspected intended target | Reason to check |
| --- | --- | --- | --- |
| `Lev.8.15`, note 2 | `Lev.30.10` | `Exod.30.10` | Leviticus has no chapter 30; label follows Exodus 29:36 |
| `2Sam.7.27`, note 1 | `Ruth.20.2` | `1Sam.20.2` | Ruth has no chapter 20; context invokes 1 Samuel 9:15 |
| `Acts.3.1`, note 1 | `.3` | `Acts.3` | Relative chapter token is not a standalone OSIS reference |
| `Rom.5.12`, note 1 | `Rom.1.à.8` | `Rom.1-Rom.8` | French “chapters 1 to 8” encoded as a nonstandard range |
| `Rom.5.13`, note 1 | `Rom.5.13.à.17` | `Rom.5.13-Rom.5.17` | French “verses 13 to 17” encoded as a nonstandard range |
| `Rom.8.9`, note 1 | `Rom.8.1.à.11` | `Rom.8.1-Rom.8.11` | French “verses 1 to 11” encoded as a nonstandard range |
| `Rom.16.25`, note 1 | `1Cor.5.32` | `Eph.5.32` | 1 Corinthians 5:32 does not exist; context invokes Ephesians |
| `Rom.16.25`, note 1 (another link) | `1Cor.2.2-1Cor.2.3` | `Col.2.2-Col.2.3` | Valid but apparently wrong-book link; context invokes Colossians 1:25–27 |

### Three other original attributes are not missing Scripture

These are **not requests to add verses or “fix” the Bible's text**:

| Note host | Original `osisRef` | Authorial context |
| --- | --- | --- |
| `Matt.23.13`, note 1 | `Matt.23.14` | Note discusses a Textus Receptus verse omitted as a separate numbered verse from this edition |
| `Acts.8.36`, note 1 | `Acts.8.37` | Note discusses a Textus Receptus addition |
| `Acts.15.33`, note 1 | `Acts.15.34` | Note discusses a Textus Receptus addition |

These original hyperlinks refer to text discussed **inside the notes** but
absent from the source's main numbered verse index. The author's notes and
textual-critical choice must be preserved. Please advise whether BPC wants
such links to remain non-navigable or to use a different intentional target,
without adding unselected verses.

## Questions for BPC

1. Can BPC confirm the eight proposed target interpretations in the table,
   and whether those link attributes are known editorial/export errors?
2. For references to the three intentionally omitted verses, is
   non-navigable source behavior intended, or is there a preferred link model?
3. If BPC issues corrected official OSIS, what edition/revision number and
   stable download should downstream distributors pin? We will audit its
   new original SHA and content before considering an update.

The original OSIS target strings and their positions were confirmed
identical in our **unpublished research** SWORD module: the link issues
predate that compilation. A real Xiphos test also demonstrated successful
activation of an *unaffected* original `Gen.2.4 → Exod.6` note link.
This does not establish that any proposed correction was authorized.

## Delivery status and owner decision

- [x] Source and individual cases independently documented.
- [x] No source text, note body, word, target, numbering or punctuation altered.
- [ ] Authorized person reviewed this proposed publisher report.
- [ ] Report actually sent to BPC; record date, method and sender.
- [ ] BPC reply, if any, attached with exact interpretation/version.
- [ ] Bible Resources owner decides whether an unchanged, disclosed
  source-faithful first release is acceptable separately from these fixes.

**Status: unsubmitted editorial draft. Public release remains blocked
pending the owner's distinct editorial and release decisions.**
