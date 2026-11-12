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

## Avoid redundant upstream re-downloads in the same stage-4 job

A reviewed manifest already identifies the source archive and original SWORD
archive using **exact SHA-256 fingerprints**. The stage runner's
`bible_intake.acquire()` obtains each once into disposable runner storage,
checks the pinned hash and safe archive layout, and passes the verified local
paths to the relevant native audit. A changed upstream ZIP **blocks** that
exact-source audit; it is never automatically re-pinned or called equivalent.

The PR audit job therefore **does not** call the separate upstream archive
`--observe-only` command before `acquire()`: doing so downloaded identical
ZIPs twice and added unverified mutable-upstream work to every stage-4 PR.
Nor does it independently re-observe the already SHA-pinned official USFX XSD
in every unrelated code PR. For **new or changed** editions, use the existing
independent [observe-originals Action](../.github/workflows/bible-observe-originals.yml)
and reviewed OSIS/USFX schema procedures **before** updating immutable
manifest pins. This change skips duplicate observation, **not source hash
validation**, standards requirements, native readback or human review.

See [Darby 2024 postmortem](DARBY_2024_IMPORT_POSTMORTEM.md) for measured
preflight and full-source timing, where the stage 4/5 optimization helped, and
what is deliberately still pending in generic fidelity work #28/#83.

## Source-bound machine receipts for subchecks 4a–4d

Every completed `stage=4` or shared `stage=4-5` machine invocation
also writes a **separate versioned `stage4-subchecks.json` artifact**.
The independent metadata questions are:

- **4a — native index:** exact occupied original-versus-SWORD source keys
  when an actual index audit is available; otherwise `PARTIAL` or `BLOCKED`.
- **4b — full numbered main text:** independently read native words,
  case and punctuation; source whitespace and any unverified original/native
  key alignment remain explicit. `DONE` is never inferred from a fast sample.
- **4c — structure:** authorial versus native paragraph/poetry start and end
  word, punctuation, event-kind and order screens; source whitespace,
  cross-verse/verse-zero mapping and non-p/q styles remain unapproved.
- **4d — stock reuse:** proven missing literal caller/type/annotation data
  **blocks** unchanged stock reuse; a clean fast sample remains
  `REVIEW_REQUIRED` and cannot approve reuse.

Each receipt includes a schema version, exact original source/SWORD ZIP
SHA-256, canonical manifest digest, Git **tool commit**, Action run URL,
machine status, bounded fixed finding codes, allowlisted integer counts
and canonical book/chapter/verse reference samples only. It also carries
explicit dependency hashes (4b requires 4a, 4c requires 4b, 4d depends
on 4a/4b/4c), while noting which full-corpus scans truly ran. The
`stage-report.json` still holds the regular stage evidence; the separate
receipt is a **metadata-only review/index document**, never Scripture or
note content.

`verify_receipts_for_reuse(...)` rejects mismatched source/module SHA,
canonical manifest, Git commit, missing/untrusted Action URL, stale
dependency hashes, rewritten machine status, missing source acquisition,
unrecognized fields, unsafe references and accidental private prose.
It returns the original **machine-only** status (including `BLOCKED`);
it cannot grant permission to publish, accept source changes or skip
another editor's review. A local `local-unpinned` receipt is never reusable.
The receipt digest is an integrity check for a **trusted GitHub Actions
artifact**, not a cryptographic signature proving the publisher's identity.

### Replay one previously verified machine receipt without re-downloading original Bibles

With the original audited run still available on GitHub Actions, choose
**Audit one Bible onboarding stage (read-only)** → **Run workflow** on the
*same exact main commit* that produced the prior metadata artifact:

- `resource_id`: the same reviewed manifest ID as the original run
- `stage`: `4a`, `4b`, `4c` or `4d`
- `reuse_run_id`: exact numeric run ID containing the previously generated
  `bible-stage-<run_id>-1` artifact with `stage4-subchecks.json`
- Optional `issue_number`: an **open** `[Import]` issue for a durable
  checkpoint, **never** an automatic approval

Or post (as repository owner only) on a new or ongoing **open**
`[Import]` issue:

```text
/bible-audit <resource-id> 4c <prior-run-id>
```

The Action downloads **only the previous text-free evidence artifact** using
the repository's own scoped GitHub Actions token. Before considering it for
reuse, the separate deterministic verifier requires exactly identical
publisher-source ZIP SHA-256, compiled-original SWORD ZIP SHA-256, canonical
manifest digest, source-acquisition proof, **same 40-digit Git tool commit**,
trusted GitHub run URL and exact prerequisite receipt hashes. A changed
original, module, manifest, code revision or dependency invalidates replay;
it fails `BLOCKED` rather than silently falling back to unverified output.
A failed/missing artifact is an error. Only the **first run attempt's**
metadata artifact is currently supported; rerun a fresh full Action when that
artifact is no longer accessible. Trusted artifact timestamps and Github's
retention period are not promises that an old upstream source is unchanged.

A successful replay reports `machine_receipt_reused_only=true` and
`new_native_scan_completed=false`, and explicitly retains the former
machine `BLOCKED`, `PARTIAL`, `DONE` or `REVIEW_REQUIRED` **without
calling `acquire()`, recompiling SWORD, downloading private original ZIPs
or rerunning expensive corpus checks**. It creates a new limited evidence
report and issue checkpoint linking to the original source run.

**Safety and limits:** This is *reusing historical exact-input machine
findings*, not a claim of new real reader inspection. It is not an
independent 4a/4b/4c/4d fresh scanner and never grants permission to reuse
a defective stock module, alter a biblical word, dismiss a discrepancy,
close the editor's checkbox, or publish. To check a different source,
SWORD module or new tool commit, launch a fresh stage 4 / combined 4-5
audit instead. Do not point `reuse_run_id` at arbitrary third-party
artifacts; the verifier accepts only source/tool-bound reports.

**Current boundary:** These are separately *reviewable* machine questions
derived from the existing one-pass stage-4 evidence, not yet four
independently executable scanners. Selective 4a/4b/4c/4d dispatch and
cross-run reuse without re-running the same reader check require a
separately validated orchestration change under [#83](https://github.com/icfmp/Bible-Resources/issues/83).
A green Action and a machine `DONE` in one narrow subcheck cannot close
any seven-stage editorial gate.

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
normal PR touching this automation uses the reviewed, pinned Darby 2024
original USFX and stock SWORD research pair as a real regression fixture.
The historically observed WEBP ZIP drift is retained separately; no upstream
revision is silently repinned, and a green CI result cannot approve Darby. No heavy
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

## CI economy: superseded PR runs

On a pull request, GitHub Actions now cancels **only superseded runs
of that same PR** when its head commit changes. This avoids repeated
full-corpus research and SWORD package installation for outdated
iterations. Owner-authorized issue-comment audits, manual `workflow_dispatch`
research and `main` validation are **not cancelled**, so their
permanent source-bound checkpoints are preserved.

This improves CI queue/retry cost. It does not waive failed native SWORD
validation, trust an external mirror, or silently accept a changed Bible
source archive.

## Fast stock note preflight — reject before expensive whitespace work

For authorial USFX plus a SHA-pinned stock `RawText`/`zText` module, the
stage-4/5 runner now performs a **bounded original-to-actual-native note
check first**. It inventories authored note-bearing verse references in
private memory, selects at most 12 references with explicit literal note
callers (preferring distinct books), and uses the existing standalone exact
SWORD key inspector to obtain real original native OSIS fragments. It
compares the matched note counts and whitespace-folded note bodies before
checking source caller labels versus the native `note n` attribute. A
proven missing/altered original caller (or an unambiguous note type
change) returns **BLOCKED for unmodified stock reuse** immediately;
it does **not** run the heavyweight word/paragraph/poetry/whitespace
proof on a candidate already demonstrated deficient. A note count/body
difference, unlike a matched-body missing literal caller, is an
**uncertain sample requiring full-corpus audit**, not a shortcut.

If the sample is inconclusive, has no literal original caller, or cannot be
read independently, the result is **REVIEW_REQUIRED**, and the existing
full-corpus audit still runs. A successful sample never means all notes
or verses match. The output contains only allowlisted diagnostic categories,
a validated source-reference ID and counts, not note text or original
caller/target values. Exact original SHA pins, verified module identity,
full text/index gates on the chosen replacement, editorial/rights approvals
and actual reader acceptance remain mandatory.

This is an *early rejection optimization*, not a full-corpus replacement or
a new Bible-specific exception. OSIS or USFM source preflight extensions
must be separately reviewed rather than silently treated as USFX.

## Material-loss gate before stock SWORD reuse

The ordinary original-USFX vs real stock-SWORD whole-corpus stage-4 run now
returns `stock_reuse_preflight`, an edition-independent decision from the
existing private reader comparison. It highlights original note-count/body
loss, missing literal caller labels, changed cross-reference note types or
explicit machine target strings, and non-whitespace Scripture differences.

A `BLOCKED` finding disqualifies **unchanged stock reuse** until investigated
or replaced by an independently audited source-faithful module. A
`REVIEW_REQUIRED` finding is *not* reuse approval: unknown note attribution,
original whitespace, headings, poetry, verse-zero material, legal identity,
reader navigation and owner signoff still have separate gates. Source text,
note bodies and original target values never appear in the receipt.

This first change reuses the already existing full private SWORD scan; it
does **not yet** avoid that scan or implement hashed per-subcheck replay.
Next work in #83 must add independently resumable inputs and a fast
feature-presence pass, not new edition-specific whitespace probes.

## One-pass stages 4+5 machine audit (experimental nonpublishing)

For a reviewed source manifest with the stock SWORD module SHA-256 already
pinned, issue this authenticated comment on the open `[Import]` issue:

```text
/bible-audit frajnd-2024 4-5
```

Or choose `4-5` for the `stage` input of the existing GitHub Actions workflow.
The command **does not create an eighth stage**. It acquires and independently
SHA-verifies the same original source and stock SWORD ZIPs exactly once,
executes the existing full source/native SWORD audit once and derives **two
distinct technical receipts** (`stage_machine_receipts["4"]` and `["5"]`)
inside one metadata-only `stage-report.json` plus one bounded
`stage-summary.md`. Each receipt retains its own `DONE`, `PARTIAL`,
`BLOCKED` or `REVIEW_REQUIRED` result. The combined report records the
canonical manifest SHA-256, current tool commit, original archive
fingerprints and whether an actual full native corpus scan completed.

A material stock-module loss still blocks that candidate even if its
Scripture prose matches. One-pass execution **does not** imply that
independently rendered book titles, source-authorial white space, note link
clicks, parallel GUI usage, rights or any publication gate are approved.
Do not tick the stage-4 or stage-5 issue checkbox from this aggregate
report alone. The original one-stage commands still work unchanged.

This reduces repeated acquisitions and full scans **only when the operator
chooses the bundle**. It does not yet implement cross-run receipt caching or
revalidate a changed source/tool without rerunning the audit. Those remain
explicitly tracked in #83.

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

## Stage 4c — source/native paragraph + poetry *opening AND closing* word positions

The generic read-only `scripts/source_native_word_boundaries.py` extends
the prior source/native **opening-kind order** test with real positions and
semantic intervals:

- It independently traverses the original SHA-pinned **USFX XML** in its
  authorial order. Each main-text `p` or `q` **open and XML close** gets
  a source book, adjacent numbered verse/intro scope, and **book-wide lexical
  word ordinal**. Generated verse/chapter labels, editorial headings, notes
  and the **separately checked** prechapter `mt` title are not counted as
  Bible main text. The independent original per-verse text collector
  cross-checks every verse exactly; a parsing discrepancy blocks this
  structural subcheck.
- During the existing whole original-stock SWORD reader scan, the same
  diagnostics independently inspect actual native `div type="x-p"`
  and `l` `sID/eID` *open and close* milestones. Native generated
  identifier values are paired **only privately**, never exported.
  Book/chapter intro markup is included as structure, but its header
  text is excluded from numbered Scripture word positions.
- A positive word-boundary result requires matching original/native word
  sequences, mapped books, p/q event kinds and **both** event endpoint
  ordinals. It rejects a moved opening, prematurely closed paragraph,
  unpaired/duplicated native endpoint or a source/native word split.
  Anonymous `TOP:N` records are independently parsed **strictly** and
  inspected for actual p/q, line/stanza and body-paragraph markup. An
  unaddressable record carrying body structure **blocks** the positional
  proof; a parseable record carrying only *other* metadata does not
  automatically invalidate already source-bound p/q word positions.
  Unknown TOP content remains separately subject to general editorial
  and native-milestone review, never globally approved. Controlled
  synthetic errors are covered by `tests/test_source_native_word_boundaries.py`.
- The public report carries only aggregate classifications, word ordinals,
  SHA-256 of structural ordinal sequences, and at most 24 safe
  book/verse reference examples. All original Scripture, note/title prose,
  arbitrary original attributes, stock raw XML and generated `sID`
  strings remain private and are discarded with the runner.
- **Important scope boundary:** matching *word ordinal* positions is not
  evidence of exact character/punctuation placement, original whitespace,
  linebreaks, original paragraph SFM/style hierarchy, cross-verse
  presentation in a specific reader, caller positions or resolved links.
  Multiple authored boundaries between the same pair of words may have
  different whitespace or punctuation offsets. They remain subjects of
  subsequent editorial/source-relative acceptance, never silently
  normalized.

If a source or native record cannot be safely mapped, the new subcheck
returns a privacy-safe **unverified/blocked** diagnostic without declaring
identical structure or overriding the existing full-text and milestone
audits. Only reviewed machine checks may be treated as mechanically
verified; the human acceptance, stage 5 and publication gates remain
independent. This is generic and not tailored to the 66-book Darby source.

## Stage 4c — authored verse boundaries versus compiled record anchors

`scripts/source_native_record_scope_triage.py` follows the independently
verified source-to-compiled **9,089 p/q opening+closing word positions**.
A source USFX structural marker may be serialized after a preceding
`v/ve` verse milestone while compiled SWORD places the identical
book-word boundary in the following numbered key or chapter intro.

The new *reusable* classifier reconstructs actual original verse start/end
**lexical ordinals** from all original indexed source-verse characters and
checks the exact original book word stream for consistency. It analyzes
both opening and closing endpoints, separately, and never executes when
the source/native book/word/start+end structural prerequisite failed:

- Distinguishes identical source/native references, the same reference
  with differing source-versus-native *scope tags*, original preceding
  versus compiled following numbered verses (and vice versa), actual
  book/chapter/verse-zero intro aliases, and source book-title boundaries.
  A shift across the same **authored interverse word boundary** is
  classified as a **possible encoding representation**, *not* an approved
  transformation.
- Keeps every unknown/ambiguous case visible: different serialized
  entry inside an authored verse, record names outside the immediate
  original word-boundary neighbors, or source zero-word/empty verses
  that make verse ownership ambiguous. Such evidence remains for
  investigation rather than being force-matched.
- Counts per-category **open and close** events and number of structural
  pairs with any record/scope discrepancy. Only up to 32 canonical
  book/verse IDs, event indices and **integer lexical ordinals** may
  appear in the resulting report; source Scripture, punctuation, notes,
  title words and original native-generated `sID/eID` values never do.
  A stable hash of metadata-only difference coordinates permits
  reproducible unchanged-source checks.
- **Do not silently approve the 9,083 originally observed
  different-scope pairs** merely because the lexical ordinal matches.
  This audit establishes which shifts can be *explained as candidates*
  by original authorial `v/ve` boundaries; it cannot establish exact
  spaces/newlines/punctuation, word-relative character offsets or
  graphical reader layout. Those require independent checks.
  Editorial source→compiled equivalence and publication remain
  reviewer-controlled gates.

Generic corruption fixtures include a moved native marker inside an
original verse, a nonadjacent key, a zero-word verse, a mislabeled
original reference, a swapped structural kind, changed word positions
and a conflicting original verse-key order. No Darby-specific
counting rule, source change or compiler normalization is introduced.

## Stage 4c — punctuation-sensitive original/stock structural boundaries

`scripts/source_native_nonspace_boundaries.py` is the next generic
stage-4c *machine diagnostic*, running immediately after independent
source/native `p/q` **word-start and word-end** parity. Exact book
text and event positions are reconstructed from the original USFX
document and the separately decoded actual stock SWORD `x-p`/`l`
milestones; neither source nor compiled Scriptures are uploaded.

**Why:** A line may start after a comma in the original and before
the same comma in the compiled record. Both positions have the
same preceding *word* ordinal, so the previous check cannot see it.

`_BookWords.resolve` now independently retains a private **book-wide
non-whitespace Unicode codepoint** stream fingerprint and each
p/q opening and closing's offset counted in that stream.
Generated bookkeeping verse separators are whitespace and therefore
excluded from this *specific* proof. The new audit:

- Requires original/native words, p/q kind and event count, and word-start/
  word-end positions to agree before reporting punctuation-level results.
- Independently requires identical **full-book non-whitespace character
  streams**, with case, Unicode codepoints and punctuation preserved
  exactly (not lowercased, NFC-folded or edited); a genuine different
  punctuation mark blocks the proof.
- Checks **each opening and closing non-whitespace codepoint ordinal**
  and returns aggregate differences plus no more than 24 canonical
  reference/ordinal-only examples, and independently computed structural
  event fingerprints. It never publishes Scripture characters, note
  bodies, unknown XML values or generated `sID/eID` identifiers.
- Includes adversarial fixtures for a moved poetic opening/closing
  across a comma **with identical word ordinals**, changed punctuation,
  only-whitespace changes, unsafe private hashes and changed word
  positions. Original text/punctuation or SWORD binaries are never
  modified or normalized to satisfy a test.
- **Explicit limitation:** matching *non-whitespace codepoint ordinals*
  is not preservation of **authored spaces, paragraph indentation,
  consecutive newline counts, poetry stanza layout or exact original
  character-byte offsets**. The original USFX and stock SWORD raw
  records already differ in whitespace; synthetically inserted
  verse separators cannot be mistaken for authored linebreaks.
  Source-authored whitespace and reader presentation therefore remain
  **PARTIAL / REVIEW_REQUIRED**, not auto-approved.

This analysis is independent of any specific edition, Greek/Hebrew
script, punctuation mark or predetermined event count. It is metadata-only
research, not publisher identity/rights or publication permission.

## Stage 4c — source-authored main-text whitespace / p-q structural gap triage

`scripts/source_native_structural_whitespace.py` performs another
**generic read-only** source-to-stock-SWORD comparison after independent
complete p/q opening+closing punctuation-sensitive proof. It reuses the
actual original authorial USFX indexed verse strings, the independently
decoded native verse strings and **original source p/q open and close
non-whitespace Unicode codepoint ordinals**. No extra archive is acquired
during the already-running full-corpus scan.

For each numbered verse, the script:

- Requires **exact identical non-whitespace source and compiled characters**
  (case, accents, punctuation, codepoint sequence). Non-whitespace
  differences **BLOCK** the whitespace classification; they are never
  normalized away to pass.
- Compares each raw Unicode **whitespace run** at the same within-verse
  **non-whitespace character gap**. It categorizes whether a changed
  run sits at an original **poetry `q` opening/closing**, an original
  paragraph `p` opening/closing, a verse start/end or a gap without
  a tracked p/q marker; and whether a source newline is absent in
  native **verse text**, a compiled newline is absent in source,
  both retain some newline but differ in run, or spaces/tabs/Unicode
  whitespace differ. It separately counts changes at verse boundaries.
- Reports only totals, a stable **hash of bounded classification
  coordinates**, and at most **24** canonical book/verse IDs and
  integer gap ordinals. It never outputs source Scripture, note bodies,
  raw whitespace strings, external input archives or native IDs.
- **Critical:** The source verse text has only the whitespace that
  the independent authored USFX reader actually collects into a
  numbered verse. It does not include the **synthetic newlines added
  as verse separators** by `_BookWords`, and cannot by itself
  determine if an XML whitespace character was intentional authorial
  indentation or publisher serialization. Likewise SWORD may express
  a poetry break with `<l sID/eID>` rather than a literal newline.
  A changed whitespace run at a matched p/q marker is therefore a
  **possible structural representation candidate**, NOT evidence of
  a preserved printed newline or a known-acceptable correction.
  Changed runs with **no p/q marker** also require review; they are
  not automatically assumed harmless.
  The next cross-tab also separates **verse-start**, **verse-internal**
  and **verse-end** whitespace changes for every marker class and
  newline category. In particular, a source newline absent from
  native verse text **without a p/q marker within a numbered verse**
  receives a dedicated `unmarked_internal_source_newline_review`
  category, while a source newline **at the end of a numbered verse**
  without p/q markup is recorded as a different
  `unmarked_source_verse_end_newline_candidate`. Neither is
  automatically approved: an XML serialization newline is not
  evidence of intended poetic linebreak, and an unmarked internal
  newline still needs source/editorial investigation.
- Existing source `p/q` typed-count, pairing, full book word order,
  character codepoint boundary, note and real SWORD native inspector
  checks remain independent. Synthetic regressions include missing
  newlines at original q opens, q closes, unmarked inline breaks,
  changed spaces, modified punctuation, altered verse identity,
  excluded source note/title prose and exact source/native whitespace.

The scope is limited to **numbered main-text verse strings** and
original `p/q` *character gap coincidences*. It does NOT audit
verse-zero intro prose whitespace, exact source paragraph/stanza
rendering, stylistic indentation, cross-verse whitespace deliberately
outside numbered verse strings, note caller/links, or reader appearance.
Those remain explicit stage 4c / 5 / 6 editorial gates. No source
or published SWORD module is ever modified.

## Stage 4c — independent original USFX XML text/tail newline provenance

`scripts/source_usfx_newline_provenance.py` independently reconstructs
every numbered original USFX verse from its **actual XML text-node and
child-tail fragments** (not a stock-SWORD approximation). It checks
**exact verse-text equality** with the separately validated USFX reader,
exact mapped book/verse coverage, and complete **original newline
gap-to-fragment mapping** before releasing *private source coordinates*
to the existing whitespace-run classifier. Parsing is strict, DTD/network
disabled; note bodies, headings, source book-title text and generated
verse-label content remain excluded exactly as in the original
main-text reader.

When the existing checker finds a source newline absent from compiled
numbered text **inside an original verse with no p/q structural marker**,
it classifies the source gap by a fixed, privacy-safe category:

- A `node.text` fragment inside an original `p`, `q` or inline
  element, versus a text fragment in an otherwise unreviewed element;
- A `child.tail` fragment after a numbered-verse/chapter milestone,
  original `p/q` element, an excluded note, a known inline element,
  or an unreviewed source tag;
- A **mixed text/tail origin** if more than one original XML fragment
  contributed a newline to the *same* non-whitespace character gap.
  Such mixed cases remain ambiguous and require review.

The resulting metadata-only report carries counts by source fragment
category, limited original book/verse reference IDs and integer
character-gap coordinates, plus the prior immutable SHA-bound overall
structural and whitespace evidence. An **independent, bounded per-origin
sample list** (`first_unmarked_internal_newline_xml_origin_references_only`)
retains at most three safe original book/verse + gap references for
each allowlisted fragment-origin category, so rare source `p/q`
`node.text` cases are not pushed out by thousands of more frequent
verse-end or inline-tail gap samples. Its reference samples are for
**editorial investigation**, not a claimed automatic approval.
**No original words, note bodies,
unknown original tag names/attribute values, native generated IDs or
raw whitespace strings leave private memory.** The synthetic fixtures
check source-verse text tampering, missing/extra newline origins,
source-note exclusion, XML fragments after inline markup, mixed
origins and independent source/compiled character continuity.

**Critical interpretive boundary:** Identifying a newline as
`tail_after_numbering_milestone` or `text_within_paragraph_element`
does **not** prove it was merely XML pretty-printing or, conversely,
that it denotes intentional poetry layout. XML node provenance is
evidence of **serialization origin**, *not authorial editorial intent*.
The independently paired SWORD p/q/`l` milestones already document
many genuine structural line breaks without literal `\\n`. Source
whitespace outside numbered verses, source/publisher stanza-style
decisions, native verse-zero introductions and actual reader layout
remain explicit **REVIEW_REQUIRED** gates. Never auto-normalize source
spaces/newlines to manufacture success.

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


## Independent publisher OSIS observation (when stock SWORD loses editorial metadata)

Some curated editions have an official publisher OSIS file *in addition to* the
eBible USFX archive and prebuilt SWORD module. Never assume these are exactly
the same edition or that independently authored OSIS has matching notes and
versification. An original compiled module may retain every Bible word but
lose original footnote caller labels.

For a reviewed publisher source, create a **research-only** manifest
`config/publisher-osis/<resource_id>.json` with its exact edition and official
HTTPS OSIS URL. The generic [publisher OSIS observer](../.github/workflows/publisher-osis-observation.yml)
can be initiated by the repository owner on the open `[Import]` issue:

```text
/bible-osis-observe frajnd-2024
```

This action downloads the official OSIS XML into the disposable runner, applies
strict HTTPS host/redirect checks and safe XML parsing, records the *observed*
SHA-256, byte length, element categories and note caller attribute categories,
and uploads **only metadata**. It publishes one permanent research observation
comment to the import issue, never a publisher manuscript, note body, arbitrary
attribute values or original archive. Add additional publisher hosts to the
explicit allowlist through a reviewed PR, not by accepting arbitrary URLs.

**Observations are NOT source pins or editorial approvals.** Compare the exact
publisher-edition OSIS with the separately SHA-pinned eBible original USFX and
actual stock SWORD: all verses, notes, caller `n` attributes, word anchors,
reference targets, paragraphs, poetry and verse-zero. An OSIS rebuild using
`osis2mod` is justified only after parity and rights are independently
verified; do not blindly choose an OSIS revision or reintroduce publisher
content that diverges from the selected edition.

Historical original stock artifacts and earlier audit results are retained.
If a later gate reveals missing authorial metadata, reopen the previously
conditional reuse-or-rebuild decision instead of publishing a module with a
known editorial loss.
