# Run Bible onboarding checks through GitHub Actions

This is the **machine-execution companion** to the
[seven-stage Bible workflow](BIBLE_7_STAGE_WORKFLOW.md).
It is **read-only research**. It does not translate, modify, normalize,
compile, publish, license or approve biblical content.

The repository already contains powerful source/native SWORD inspectors.
`scripts/bible_stage_runner.py` invokes them in a repeatable, bounded
**one-stage-per-workflow-run** arrangement. Source ZIPs remain in the runner's
temporary directory, never in logs, Git artifacts or the published catalogue.

## Prepare an edition manifest once

Each future Bible is represented by one reviewed file:

`config/bible-intake/<resource_id>.json`

It must satisfy `schemas/bible-intake.schema.json` and contain:

- Unique resource ID, real title, exact edition and source language.
- Original provider and archive URLs from a hardcoded HTTPS host allowlist.
- **Exact SHA-256 hashes** of the original authorial source ZIP and official
  SWORD module ZIP are mandatory **before stages 2–6 download anything**.
  During **stage 1 only**, `sha256: null` explicitly means **not yet pinned**;
  this allows a safe metadata-only edition/rights checkpoint without inventing
  fingerprints. `sword.module_id: null` and `sword.driver: null` similarly
  mean **not yet inspected**. The stage-one runner performs **no network
  acquisition**, and all later stages fail closed *before* opening an archive
  if any of these identities are still unknown. Hashes must be independently
  recorded and reviewed before continuing; stage 1 cannot approve publication.
- `source.format`: `USFX`, `USFM`, or `OSIS`; for OSIS add the
  exact XML `source.member` in the ZIP. USFX needs a reviewed explicit
  book-name crosswalk. Neither unsupported markup nor ambiguous
  source-to-compiled verse indexing is silently corrected.
- Original SWORD ID, actual `RawText` or `zText` driver,
  and two or more representative book/chapter/verse probes.
- A rights-evidence URL and rights review status. **`research_only`
  is mandatory**: even after a technical report passes, this file does
  not grant redistribution or editorial permission.

The `frajnd-2024` file **began** as a stage-one-only preliminary manifest
with explicit `null` SHA-256 and uninspected SWORD identity. Its original
USFX/SWORD hashes and actual `zText`/`Luther` stock identity were subsequently
observed by [Action 42808540898](https://github.com/icfmp/Bible-Resources/actions/runs/42808540898),
pinned in [PR #65](https://github.com/icfmp/Bible-Resources/pull/65) and independently reacquired in
[stage-2 Action 42809483184](https://github.com/icfmp/Bible-Resources/actions/runs/42809483184).
eBible's linked authorial source is USFX; original publisher BPC separately
provides 2024 OSIS XML as an independent editorial cross-check. The revised
2026 DarbyR is excluded.

The existing `webp-research` file is an archived **research example**,
not a second Bible approved for public release. It is pinned to the
historically audited WEBP USFX and original eBible zText archives. Existing
source-only verse and note/canon differences are *expected to block full
fidelity*, not to be hidden by special cases.

## Observed upstream revision drift — nonpublishing WEBP test fixture

The source archives used in the 2026-11-09 WEBP research **changed on the
eBible server**. The initial pinned fixture correctly failed instead of
accepting changed material as identical. A read-only, HTTPS-allowlisted
observational run ([PR #59, workflow #42799441256](
https://github.com/icfmp/Bible-Resources/actions/runs/42799441256))
recorded only file sizes and SHA-256 values:

| Archive | Historical SHA-256 (2026-11-09) | Newly observed SHA-256 (2026-11-10) |
| --- | --- | --- |
| Original `engwebp_usfx.zip` | `66f99b22a380d8ef8dbd9d401806fc02be3650e5fe3dbb0cec4d9693b53e1e44` | `f678047c4177451b476c7f25e18ac3798d6722c25d474a56440b0ab8e2d7d84e` |
| Original `engweb2025peb.zip` | `53d45377d1aa376f483aded415b6d122b7cbe6795baddc49dae6574e304b8810` | `341fa8898cdbcdd28b743d3c28b663abb181644d3a5ec4420467fad487ba7ce8` |

The **research-only fixture** was deliberately updated to the observed
2026-11-10 hashes to exercise the orchestrator. This is **not**
proof that either publisher edition, words, notes or canon remained the
same as the historical experiment, nor a curated revision or a publication
authorization. A real future candidate must use its own reviewed
manifest and independent edition/source review before anything is released.

## Observe unknown source fingerprints without trusting mutable upstream bytes

A **separate read-only observation** is available before committing a real
SHA-256 pin. On an open `[Import]` issue, the repository owner posts:

```text
/bible-observe frajnd-2024
```

The [original-archive observation workflow](../.github/workflows/bible-observe-originals.yml)
downloads both declared HTTPS archives into disposable runner storage, verifies
ZIP safety, records their exact SHA-256 and stock SWORD `.conf` metadata, then
discards all original bytes. Only metadata are uploaded, and the workflow
automatically posts a permanent **UNAPPROVED OBSERVATION** report to the issue.
No publisher text is logged or published. The report identifies *observed*
upstream bytes, not verified editorial equivalence or a new public release.

**Review the publisher edition and this receipt before updating the
research manifest.** A changed upstream ZIP is not silently an equivalent
revision. A later stage 2 re-downloads both originals with strict SHA-256
checking; drift blocks the run. Do not manually tick stage 1 merely because
the fingerprint-observation workflow succeeded.

## Run it

**Recommended — start from the Bible's issue (including from ChatGPT):**

Post the following exact command as a new top-level comment in an **open
`[Import]` issue**, from the repository owner's GitHub account:

```text
/bible-audit webp-research 4
```

The workflow listens for owner-authored `issue_comment` events on
`main`, verifies the issue type, and parses only a strict resource ID
and integer stage 1–7. It then runs without keeping the ChatGPT session
open and automatically posts the metadata-only summary back to that
issue. Replies by other users, malformed commands, comments on PRs, and
non-import issues are ignored. The GitHub connection used here posts
comments as the repository owner, so the assistant can initiate an
approved stage through the same issue-comment action; it need not have
a direct `workflow_dispatch` permission.

**Alternative — manual dispatch through GitHub Actions:**

Open [Actions → Audit one Bible onboarding stage (read-only)](
https://github.com/icfmp/Bible-Resources/actions/workflows/bible-staged-audit.yml),
select **Run workflow** on `main`, and provide:

- `resource_id`: the filename without `.json` (e.g. `webp-research`).
- `stage`: **1** through **7**; each execution checks just one bounded stage.
- `issue_number` (optional): the corresponding open **[Import]**
  issue; the workflow posts a short permanent *evidence* comment there.

Every run writes `stage-report.json` and `stage-summary.md` as
**metadata-only** artifacts (90-day retention), and shows the report in
the GitHub Actions run summary. If an eligible import issue is provided,
the comment holds the result beyond artifact retention, with a link to the
specific run. **It never checks the issue's box automatically**: a
complete stage gate also needs any mandatory source, rights and editorial
review documented in the issue. A failed download or a malformed source
blocks the job; a completed *diagnostic* can legitimately return
`PARTIAL`, `BLOCKED` or `REVIEW_REQUIRED` while the workflow execution
itself succeeded. A green GitHub Action is **not** a publication approval.

For local development:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_bible_stage_runner.py' -v

mkdir -p /tmp/bible-report
python scripts/bible_stage_runner.py \
  --resource-id webp-research --stage 1 --report-dir /tmp/bible-report
```

For stage 1, no network fetch occurs. An unpinned manifest may pass
structural validation, but the stage-one report lists all unresolved pins,
edition identity and rights decisions as `REVIEW_REQUIRED`. **Never** mark
the checkpoint done merely because its GitHub Action run is green.

For stage 2 and above, network fetches always verify the pinned original
archives in the temporary work directory. Stages 4–5 require stock
`libsword-dev` C++ inspectors, which the GitHub workflow compiles;
stage 6 requires `diatheke`. An original OSIS stage 3/4 requires the
official, pinned schema automatically fetched by its existing approved
helper. Source and original SWORD binary never appear in the artifact.

## Automation coverage — honest limits

| Stage | Currently automated and recorded | Remains outside automated approval |
| --- | --- | --- |
| 1. Edition / rights | Config field validation and official provider URL review | **Human** textual/edition identity, duplicate baseline, legal/notes/Strong rights |
| 2. Originals | Bounded HTTPS acquisition, redirect allowlist, exact SHA-256 and safe source/SWORD ZIP preflight | Human verification of publisher source selection when first pinned |
| 3. Authorial source | Original USFX full source-native structure and verse inventory, exact pinned official USFX XSD; USFM source inventory; original OSIS XSD and verse inventory | Full authorial publisher-edition review, conversion parity if transformation is actually used |
| 4. Native vs original | Actual native `RawText`/`zText` whole-corpus comparison for **USFX** with explicit book crosswalk; OSIS native index comparison | A generic USFM conversion and full OSIS→SWORD semantic comparator; edition/canon and source-only verse conflicts |
| 5. Editorial structure | USFX numbered-note body/type/target **diagnostics** on the real native corpus | Word-position anchors, resolved source links, book introductions, poetry, Strong ordinals if present, authoritative signoff |
| 6. Reader trial | Isolated standard SWORD ZIP installation and deterministic stock `diatheke` readbacks | Another independent reader and manual visual/parallel acceptance |
| 7. Publication | Deterministic **review-required** gate, with *no* publish action | Explicit owner approval, release PR, normal repo CI, GitHub Release + Pages and live HTTP check |

An unsupported format or missing evidence is reported as **BLOCKED** or
**PARTIAL**, not silently downgraded to success. Stage 4 can report
`BLOCKED` for the original pinned WEBP anomalies even when its
stock-SWORD extraction was performed correctly.

### Resuming after a chat or Actions interruption

1. Read the resource's import issue and its last dated audit checkpoint.
2. Verify the linked run, source SHA-256 and Git commit. If the manifest
   or audit script changed, the previous result is not a certificate for
   the new bytes.
3. Re-run **only the necessary stage** with the same reviewed inputs.
   A later stage may re-download the originals to an isolated runner and
   independently re-verify their hashes; this is deliberate, not loss of
   editorial progress.
4. Keep prior completed stages in the issue, record a new comment and
   update the checkbox **only once all requirements of that stage are met**.

A ChatGPT session is **not** kept alive and is not automatically notified
at the end of an Action. The assistant can **start** an eligible run by
posting an owner-authored `/bible-audit <resource-id> <stage>` comment
in the appropriate issue, but a later message is required for the
assistant to return and interpret the completed action. The issue and
run URLs preserve the exact checkpoint for the next conversation. A
normal PR touching this automation triggers the existing pinned WEBP
research proof, without approving its original edition. No heavy
research step should be run in a long-lived chat.

## Full-corpus whitespace differences: diagnostic, not silent normalization

For a source-native `USFX` to existing-stock-`zText` comparison, stage 4
already independently checks all occupied native reference keys and compares
the entire mapped text sequence. A complete match after whitespace folding
**does not** establish exact textual whitespace or original paragraph/poetry
layout equivalence. Source and stock module always remain unchanged.

`scripts/maintext_whitespace_patterns.py` extends that same private pass
with **aggregate, source-content-free evidence** for all verses classified
as `whitespace_only`:

- number of verses with leading/trailing versus internal changes;
- newline and tab changes on each side, and Unicode spaces (including NBSP);
- increasing/decreasing/same-length whitespace runs;
- up to four **verse reference IDs** per category, never Scripture, note body,
  raw strings or literal whitespace excerpts.

The observation is derived from the separately pinned original and the
independently read native entries in disposable runner storage. If a word or
punctuation changes, the strict classifier **must not** treat it as
whitespace-only. The report is included in the metadata-only stage-4 Action
receipt. This enables a precise decision about whether boundary trimming is
a stock compiler behavior or whether source-internal layout was altered.

The separate `scripts/native_sword_markup_census.py` also inspects the
**actual safely parsed raw SWORD XML entries** in the existing private
full-corpus pass. It counts known original compiled XML tags, attributes by
**name only**, paragraph/line/poetry/milestone/title/note/reference groups,
and how many numbered verse entries contain each group. Unknown tag and
attribute names are reported as counts only; original attributes (including
note callers and raw reference targets), Scripture and raw XML are never
uploaded. The markups recorded here describe **compiled evidence**, not a
claim that an authored USFX `q` or `p` was preserved with the same
boundaries or position. Cross-verse structures and verse-zero introductions
still need their own audit and manual editorial review.

**Stage 4 stays `PARTIAL`** while any original whitespace/layout remains
unverified, including when all words and punctuation match. Stage 5 must
evaluate editorial paragraphs/poetry and note caller/anchor/target parity.
Never automatically rewrite, strip or approve whitespace or invent verse
mapping exceptions to obtain a green report. Any later acceptance needs
the exact report link and source-scoped explanation recorded on the import
issue.

## Stage-4 subchecks and provisional source/native structural anchors

Step 4 is split **internally** into 4a (stock identity / complete reference
index), 4b (full numbered main text), 4c (whitespace and major editorial
structure triage), and 4d (stock reuse versus source-faithful rebuild decision).
The top-level workflow, issue checklist and user-facing progress remain **seven
stages**. See [the bounded 4a–4d checklist](BIBLE_7_STAGE_WORKFLOW.md).

The original-USFX structural anchor probe is a *diagnostic precursor* to a
source-relative paragraph and poetry proof:

- It inventories source USFX `p` and `q` **start markers**, preserving the
  preceding and next actual numbered verse reference as evidence, without
  assuming the marker lies within the next verse.
- The independently decoded, actual original stock SWORD raw XML records
  allowlisted `div`/`milestone` structural `type`/`subType` categories,
  actual start/end vs container markup, and whether markers occur before the
  first, inside, or after the last numbered main-text word.
- Source start markers between two numbered references also require an
  **interval screen**, not only an exact next-reference match. A native marker
  might be attached to the preceding numbered verse, or a verse-zero/intro
  entry (the latter remains out of scope for this screen). The report counts
  next-verse, previous-neighbor-only, and neither-neighbor cases, with only
  bounded source reference IDs. A neighboring native marker is **never**
  claimed to be the corresponding authored event without validating the
  exact type/word position/order and cross-verse semantics.
- An original source structural start at a **chapter opening** has no
  previous numbered verse within that chapter. The native SWORD inspector
  therefore also privately parses actual **occupied book/chapter verse-zero
  intro entries** exposed by the independent native reader. It records
  only allowlisted intro div/line styles, bounded reference IDs, counts
  and parse failures (never raw intro Scripture, headings, source titles
  or unknown attribute values). It distinguishes native intro markers,
  chapter openings without observed parseable intro markup, and genuinely
  intra-chapter intervals missing both numbered neighbors.
- An intro with malformed/unbalanced XML is **unverified**, not repaired
  with a permissive parser. Intro co-occurrence is still not position-exact
  source↔SWORD paragraph/poetry identity. Missing style information can
  reflect open markers spanning multiple references; stage-5 structural
  acceptance is not waived.
- Source next-verse anchors are screened against the set of native verses
  containing `div` or `l`/`lg`/`lb`. A corresponding verse key is **not
  proof** of matching markup semantic meaning, source layout position or
  cross-verse scope. Any apparent missing marker is a *review candidate*,
  not automatically a data corruption.
- Only allowlisted markup styles, bounded reference IDs and aggregate counts
  appear in the report; unknown raw `type`, `subType`, note values, Scripture
  and raw XML never appear in a GitHub artifact.
- Missing source/native correspondence, verse-zero/intro scope and exact
  original paragraph/stanza boundaries still require more complete
  **source-grounded proofs** and human editorial review. This screen never
  returns publication/editorial approval or changes source text.

The step-4 stage stays **PARTIAL** until the whole stage gate is reviewed.
Step 5 retains detailed caller/anchor/target and exact editorial structure
comparison; a read-only diagnostic does not waive those requirements.

## Stage-4c: actual compiled SWORD milestone-ID closure (not source layout parity)

The read-only `scripts/native_milestone_pair_audit.py` joins the **already
full-corpus, independent SWORD native reader**. In the original engine's
ordered stream, it strictly parses all occupied numbered and verse-zero
XML entries privately and checks matching `sID`/`eID` *identifier values*
on structural `div`, `l`, `lg`, `milestone`, `p`, `q`, `lb`.

- A count equality alone is insufficient: every close must find an active
  opening of the same tag and ID, with duplicate active identifiers,
  orphan closings, dangling openings, cross-book boundaries, conflicting
  types and non-LIFO/crossed nesting recorded as distinct evidence.
- Intro-to-numbered, numbered-to-numbered and intro-to-intro pair counts
  are preserved. Raw identifiers, Scripture, note contents, unknown
  attribute values and raw XML are **never present** in the saved receipt.
  The report retains only counts, fingerprint, and bounded reference IDs.
- Body content of `note` and `title` is **excluded**, as those have
  separate annotation/editorial checks. Non-addressable TOP records are
  explicitly flagged **unverified**, never silently discarded.
- An actual compiled `sID`/`eID` proof verifies the internal integrity
  of the *stock module*, **not** that the module has preserved the correct
  USFX author's paragraph/poetry starts, source type hierarchy, every
  line-break location, or notes/word positions. The next check must align
  source and compiled semantic event **order/position** to make that
  claim. Do not auto-normalize original whitespace or publish on
  matching milestone counts alone.

**Do not tick stage 4c or stage 4/7** until exact source-relative structure
issues are reviewed. Stage 5 retains source-native note/caller/target and
final typography checks. No change to published Bible modules or rights.

## OSIS overlapping hierarchies and typed paragraph milestones

**Do not treat every `div` in a SWORD fragment as an authorial paragraph.**
CrossWire's [osis2mod transformation documentation](
https://wiki.crosswire.org/Osis2mod) distinguishes:

- original paragraph `p` converted to `div type="x-p"` with generated
  `sID/eID` endpoints;
- compiler-generated `div type="x-milestone" subType="x-preverse"`
  delimiting inter-verse/prepended content, **not a source paragraph**;
- optional book/book-group divisions and other typed editorial containers.

The [CrossWire OSIS milestone documentation](
https://wiki.crosswire.org/OSIS_Bibles#OSIS_Milestones) also describes
the **overlap** of verse and document hierarchies. An all-tag global stack
may see valid `div`/poetry/verse interleavings as "non-LIFO"; this alone
does not prove a malformed compiled module.

The compiled ID audit now distinguishes **interleaving between different
element tags** (report-only evidence) from **overlapping ranges of the
same tag** (explicit structural review finding); it records exact
`sID/eID` matches independently of both. Cross-book ranges are
reported with bounded *opening and closing reference IDs* plus
allowlisted type categories, because top-level book-group or testament
regions may legitimately span several books. Such scopes still require
an independent authorial/compiled source comparison.

For `div`, the audit separately counts matched **allowlisted**
`x-p` paragraph pairs, `x-milestone` technical/preverse pairs,
`book` and `bookGroup` divisions, and unknown types. Unknown
original attribute **values** are never copied to public reports.
The two anonymous native TOP entries are parsed privately to distinguish
actual structural milestones from other non-addressable content; neither
entry is used to invent a source reference.

**This remains a compiled-side diagnosis.** A complete match of all
native IDs cannot alone establish that original USFX paragraphs, headings,
poetry or notes were preserved at the correct word positions. The source
relative event/order audit and editorial gate must still be reviewed
before checking 4c or 4/7. Never patch source or hash pins just to pass
a test.

## Typed authorial `p` versus stock SWORD `x-p` — per-book research

A complete numbered-text and correctly paired native-ID inventory is still
insufficient to prove every original USFX paragraph survived conversion.
The [documented osis2mod mapping](https://wiki.crosswire.org/Osis2mod)
turns `p` into *typed* `div type="x-p"`; it also generates technical
`div type="x-milestone"` wrappers. Never compare the source `p` total
with **all** native `div` elements or claim the mere presence of a
neighboring `div` proves an original paragraph was retained.

The generic `source_native_paragraph_counts.py` audibly counts all
authorial `p` nodes **per original book**, explicitly inventories
those before the first book verse, before the chapter, at chapter starts
and inside footnotes, then compares each with **exact `x-p` paired-ID
counts in the stock SWORD original reader**. It outputs aggregate counts,
one bounded per-book anomaly example for each mismatched book and a
metadata-only deterministic book-distribution digest. No biblical words,
source note bodies, arbitrary types, markup values or ZIPs are retained.

Matching per-book counts are only **necessary**, never sufficient:
paragraph event order, relative word position, source type semantics,
verse-zero/non-numbered titles and paragraph start/end spans need
independent source-grounded checks. A source/stock difference of exactly
one paragraph per book is an **investigation finding**, not permission
to insert invented paragraphs or waive the discrepancy.

The simultaneous native overlap diagnostic distinguishes same-tag /
same-type overlapping milestone ranges from same-tag / *different*
type overlaps (`x-p` versus `x-milestone`). The latter are
explicit review findings, not automatic proof of corruption or faithful
markup. The **seven-stage progress and stage 4c gate remain unchanged**.

## Source pre-chapter prose against actual stock SWORD book introductions

The source-only `audit_usfx_book_prefaces` records whether every USFX
paragraph **before chapter one** contains authorial words, markup, notes or
attributes, without exposing text. The original BPC Darby 2024 test showed
**66 nonempty original prefatory p elements**, one per book; these may not
be silently ignored as empty paragraph markers simply because the compiled
`div type=x-p` count is 66 lower.

`scripts/native_book_intro_screen.py` reuses that source-only classifier
and independently inspects **actual stock SWORD book-level** and
**first-chapter verse-zero** intro records already extracted by the
private native corpus reader. It uses strict XML parsing and records:
- Actual native intro presence, parse failures and allowlisted div/title
  structures; unknown native attribute values are categorized, not leaked.
- Whether original prechapter paragraph prose appears **contiguously**
  in either raw native intro text after **whitespace-only folding**;
  no case, punctuation, word or character substitution is accepted by this
  weak comparison. Original preface and native title/note contents remain
  private and are discarded.
- Bounded original/native book IDs whose original preface prose was not
  found in inspected intro locations.

A further scope-specific check looks **inside each native book-intro
`title` element**, rather than claiming that any adjacent intro text
proves preservation. It separates the following outcomes with metadata-only
counts and bounded book codes: exactly one title containing precisely the
source prefatory prose (after whitespace-only folding), a title containing
it with additional text, duplicate matching titles, source prose present
only elsewhere in the book intro, or prose not found at all. Original
authorial text, title contents and unknown native attribute values remain
private. Even a one-to-one lexical match to a native title **does not**
establish that source `p` paragraph *style*, heading hierarchy,
source-relative placement or authorial typography were preserved: those
remain editorial checks for stage 4c/5.

**A contiguous text occurrence is not an exact structural parity
certificate**: a heading may be moved, duplicated, rewrapped, placed in
another (uninspected) scope or rendered differently. Missing intro text is
an investigation finding, not proof that the user-visible Bible has no
book heading. The 4c and step-5 editorial gates remain open pending an
actual source-relative position/order/type review, including verse-zero.

This is generic across edition/versification and does not modify original
USFX/SWORD archives, publication content, references, source hashes or
reader behavior.

## Original USFX prechapter `p` styles versus compiled SWORD book titles

The [official eBible USFX XSD documentation](https://ebible.org/usfx/usfx_xsd.html)
specifies that a `<p>` element can mean a normal paragraph **or a heading
or title**, according to its original `sfm` attribute. Counting all
`p` as ordinary paragraphs silently loses authorial style semantics.

The generic `audit_usfx_book_prefaces` in
`scripts/source_native_paragraph_counts.py` now inventories the original
source `sfm` for each paragraph **before the first chapter**. It preserves
only an allowlisted public USFM code or an explicit
`other_unreviewed_style` category; the original `style` attribute
content, unrecognized `sfm` values and Scripture/title words never appear
in artifacts. Styles are grouped conservatively as known *book title*,
*section heading*, *other heading*, *body paragraph*, *implicit p*, or
*unreviewed*. The original `style` and `level` attribute **presence**
and potentially conflicting `sfm` vs `style` values are counted without
publishing those values. An explicit title-family SFM is useful source
evidence, **not** automatic authorization to transform that element into a
SWORD `title`. Missing or unknown styles stay visible and require review.

The original/compiled book-intro title **prose** is compared separately in
`scripts/native_book_intro_screen.py`. A successful 66/66 lexical title
match is not by itself proof of source-style equivalence or of ordered
paragraph and poetry boundaries. The remaining source→compiled
position/typography review in 4c and 5 is not waived. No original file or
native SWORD module is modified.

## Stage-4c source↔native *ordered body event-kind* comparison

`scripts/source_native_ordered_body.py` compares original USFX main-text
structural **opening order** by original mapped book against the actual
stock SWORD `sID` opening stream from
`native_milestone_pair_audit.py`:

- Authorial **`<p>`** body paragraph starts map to compiled
  **`<div type="x-p" sID="...">`** openings. Authorial **`<q>`**
  poetic-line starts map to compiled **`<l sID="...">`** openings.
  It compares entire ordered sequences of these two **types** within
  each original book, not only their total counts. Native values of
  generated structural IDs are never returned.
- Original `p` **before chapter one** is excluded from the *body sequence*
  **only** when its original `sfm` is an explicitly recognized book-title
  style. Its exact original text and its native SWORD `title` match are
  independently inspected, and the exclusion is counted. An ordinary or
  unknown-styled original prefatory `p` is never silently discarded.
  Paragraphs inside annotation notes are counted in their own category,
  not confused with main Scripture body structure.
- The report records complete per-book kind-sequence equality status,
  source/native event count totals, source/native kind-sequence hashes,
  and at most 24 reference-only examples of missing/extra/reordered
  openings. It publishes **no** verse words, title/footnote bodies,
  native generated structural IDs or unknown XML attribute values.
  Ordered book mismatches remain review candidates: they are **not**
  automatically corrected to satisfy a test.
- This is strictly **order and kind**, *not* a certificate of exact
  source/native word-relative starts/ends, individual paragraph span,
  stanza boundaries, line/verse-zero placement, full source SFM styles,
  typography, whitespace or CrossWire reader rendering. These require
  independent source-bound positional proof and editorial acceptance;
  stage **4c** remains **PARTIAL** until those gates are considered.
  Stage 5 separately verifies note bodies/callers/word anchors and links.

When an independently inventoried source has unresolved book/verse
structure or an ambiguous crosswalk (for example, a historical research
fixture), this **additional order check** returns an explicit, text-free
`blocked_original_authorial_source_scope_or_structure` diagnostic.
It does **not** substitute an empty sequence, silently omit original
books, invent ordering, or stop unrelated existing full-source tests.
The stage-four machine result lists that missing structural gate and
cannot be interpreted as source-to-compiled order fidelity. Original
source discrepancies require investigation under the generic issue and
must never be suppressed merely to make CI green.

The original pinned eBible archives remain untouched, and no module is
published by this audit.

## Safety and publication separation

- GitHub workflow uses `contents: read` for the audit job.
  A separate manual-run-only notification job has narrowly scoped
  `issues: write` to comment on an existing open `[Import]` issue.
- Repository/source material is never committed by this Action and no
  automated dispatch can update a SWORD ZIP, bump the module version,
  set `quality.status=approved` or deploy Bible text.
- Source download hosts are a source-controlled allowlist; archives must
  be HTTPS, bounded, complete, unchanged by redirection and SHA-256-pinned.
  ZIP files are preflighted for path traversal, duplicate member paths,
  symlinks and size limits before a separate isolated reader uses them.
- Even when original notes or Strong metadata are missing from a source,
  no generated additions, content rewriting or automatically invented
  edition relationships are permitted.
- Audit artifacts contain counts, hashes, code and reference IDs only.
  They are evidence of *which controls ran*, not independent certification
  of the publisher's identity or ownership.
