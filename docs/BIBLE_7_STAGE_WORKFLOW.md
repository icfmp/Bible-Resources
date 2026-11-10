# Seven-stage Bible onboarding — resumable, evidence-gated workflow

**Scope:** every **new Bible edition** in Bible Resources. Commentaries have
different annotation and coverage semantics and need their own validated
specialization; do not pretend this Bible checklist certifies them.

**Goal:** a predictable **7-stage** route from an upstream candidate to a
verified release. The project owner can always see the current stage,
the number completed, what is blocked and what comes next. This is the
operational front door for the detailed [resource onboarding playbook](
RESOURCE_ONBOARDING_PLAYBOOK.md) and [generalization issue #28](
https://github.com/icfmp/Bible-Resources/issues/28). It **does not**
claim that the full generic fidelity pipeline is already implemented.

## GitHub Actions execution and recovery

Use the [staged Bible audit GitHub Action](BIBLE_STAGE_AUTOMATION.md) to run
**one** checkpoint remotely, preserving the original resources in runner
temporary storage and uploading only metadata-only evidence. The operator
provides a reviewed `config/bible-intake/<resource_id>.json` manifest,
chooses an individual stage (1–7), and optionally an `[Import]` issue
number for an automatically posted permanent checkpoint comment.
**Stage 1 may use explicit `null` placeholders for archive SHA-256 and
uninspected SWORD ID/driver**, because this stage performs no network
acquisition. All stages 2–6 reject those provisional identities **before
any download**; never fabricate hashes simply to start stage 1.

Some existing automated components are **diagnostics, not yet complete
gates**, especially USFM/USFX→OSIS conversion parity, source/native note
anchors, resolved reference targets, Strong ordinal/poetry boundaries,
second-reader visual acceptance and final owner editorial approval.
A completed Actions execution can therefore report `PARTIAL`,
`BLOCKED` or `REVIEW_REQUIRED`; the issue progress checkbox must not
be checked until the **whole gate** is independently evidenced.

## The seven checkpoints

| # | Stage | Deliverable to save on GitHub | Gate before advancing |
|---|---|---|---|
| **1/7** | **Select edition and rights** | Exact title, edition, provider, source/official SWORD alternatives, text/notes/enrichment licenses, and reuse-vs-rebuild decision | Sources and rights are evidenced; unresolved redistribution rights = **BLOCKED** for publishing, and no redistribution |
| **2/7** | **Acquire and pin originals** | Publisher revision, original archive URLs, exact archive SHA-256, source format/canon/v11n and separately acquired stock SWORD metadata | Every used original is reproducibly identified; immutable input and rights records saved without committing restricted originals |
| **3/7** | **Validate authorial source** | Official OSIS schema/structural report, original verse-order/heading/poetry/notes inventory, **USFM/USFX→OSIS parity when conversion is required** | Unknown elements, missing notes, ambiguous source identities or unverified conversion cannot be called passed; use source-native formats when possible |
| **4/7** | **Build or reuse SWORD, check index and text** | Standard isolated candidate module, SWORD registry/native keys vs original source keys, full numbered main-text word/punctuation comparison, documented source-only verses/merges | No unexplained missing/reordered text or keys; differences are evidence-classified and approved, never silently corrected |
| **5/7** | **Verify annotations and editorial structure** | Complete report for note body/type/caller/**position**, original explicit cross-reference targets, headings/paragraphs/poetry/verse-zero, Strong/lemma alignment **if present** | No undocumented loss/movement of original editorial data; unresolved findings stay BLOCKED; genuinely absent features are explicitly marked N/A with evidence |
| **6/7** | **Test the actual reader package** | Exact candidate ZIP checksum; install/readback with stock SWORD/diatheke plus another independent reader where available; representative passages, independent/parallel readings and recorded limitations | Executed tests linked; unavailable GUI/client checks remain **NOT TESTED**, never a fabricated success. Blocking reader defects prevent release |
| **7/7** | **Approve, publish, and verify** | Owner editorial/rights sign-off, final provenance and known-limitations record, immutable release and source/payload checksums, official catalogue snapshot and successful Pages publication, external endpoint check when available | No public claims before actual approval and publication; distinguish successful workflow, GitHub release, external HTTP availability and app adoption |

For an already satisfactory **official SWORD module**, stage 3's conversion
and stage 4's rebuilding can be **N/A** if justified by a verifiable
original-source/official binary audit. The **index, content, notes and reader
checks still apply**. For an edition without Strong's numbers, don't create
them; record the Strong check as N/A, not as a passed lexical audit. A lack
of source-level evidence is a blocker, never proof of equivalence.

## Step 4/7: four bounded internal checkpoints (still ONE of seven stages)

Experience with the second real Bible (BPC Darby 2024) showed that `4/7`
is too heavy to execute, review, and troubleshoot as one indivisible pass.
Keep **seven top-level stages**, but track four **internal subchecks** under
the single existing stage-4 checkbox on each resource issue:

| Subcheck | Evidence | Must be demonstrated before it can be checked |
| --- | --- | --- |
| **4a. Native module and reference registry** | Original stock ZIP, `.conf`, engine/native v11n, source↔native book mapping and every numbered key | Stable module identity and complete source/native index; no missing, duplicate, reordered or silently merged references |
| **4b. Full-corpus numbered main text** | Original↔native every-verse words, punctuation, case and exact SHA-based provenance; excluded notes and headings counted independently | No undocumented non-whitespace differences; any exact character differences classified rather than auto-corrected |
| **4c. Whitespace and structure triage** | Actual source/native newline and spaces, paragraph/poetry/intro markers, positions and cross-verse scope | No unexplained *material* loss; if a native representation differs, record precisely why and defer detailed editorial positioning to stage 5 |
| **4d. Reuse-or-rebuild decision** | Exact upstream/module fingerprints, relevant test runs and documented differences/risks | Justified stock-module reuse or a separate, source-faithful rebuild plan; no exception invented for this edition, no owner publication approval implied |

Only after **all four subchecks** have evidence may the parent issue's
`4/7` checkbox be ticked. Individual internal successes can be recorded
in the import issue without incrementing the `X/7` total. A subcheck can
be `DONE`, `PARTIAL` or `BLOCKED`; preserve the evidence and report the
next *one* concrete action. Prefer one small generic PR or read-only Action
per independent issue rather than repeatedly modifying all four subchecks.

**Boundary with step 5:** step 4 assesses integrity and suitability of the
SWORD text/index package. It does **not** sign off all original note bodies,
callers, lexical positions, explicit link targets, paragraph/poetry exact
boundaries, or full verse-zero presentation: those detailed, source-relative
editorial comparisons belong to **step 5/7**. A flagged risk in 4c must remain
visible and block the *relevant* acceptance gate in 5, even when a limited
step-4 SWORD text/index check can be approved.

**Future editions:** use the same four subchecks for any translation and
native `RawText`/`zText` driver, never add hard-coded Darby/Segond
reference counts or re-label a legitimate source difference as a formatting
fix. Additional internal breakdowns should be introduced **only when a
repeatable bottleneck is demonstrated**; do not inflate the seven-stage
workflow itself.

## One progress tracker — no mystery number of steps

Create **one GitHub issue per Bible** using the
[Import a resource issue template](../.github/ISSUE_TEMPLATE/import.yml).
The issue body is the **single current status**; a short checkpoint comment
is added after *each* completed or blocked stage. Example:

```text
Resource: <publisher edition and source>
Progress: 2/7 DONE — current stage 3/7: Validate authorial source
Status: IN_PROGRESS  (or BLOCKED / READY_FOR_OWNER / COMPLETE)
Last verified checkpoint: stage 2/7 — <commit / PR / workflow link>
Next action: <one concrete action>
Blocker: none  (or exact blocker, responsible party, workaround if any)

[x] 1/7 Select edition and rights
[x] 2/7 Acquire and pin originals
[ ] 3/7 Validate authorial source
[ ] 4/7 Build/reuse SWORD; compare index and words
[ ] 5/7 Audit notes, references, structure and optional Strong
[ ] 6/7 Reader tests and exact package
[ ] 7/7 Owner approval, publish and verify
```

**Do not tick a checkbox until its gate is evidenced.** Never tick a
partially finished stage. If a stage fails, keep its number, set **BLOCKED**,
preserve prior checkpoints and describe the next diagnostic. When a stage
contains several genuine technical problems, use **small sub-PRs within
that same stage**; this does not turn the workflow into 20 stages.

## The checkpoint transaction (at EVERY stage)

1. **Read current GitHub state first**: parent issue, last checkpoint
   comment, linked merged PR(s), their exact commits and CI. Never infer
   progress from chat history alone.
2. **Work on one bounded concern**. Preserve immutable originals, exact
   SHA-256 and prior approved releases. Do not overwrite the published
   SWORD module, source evidence or a signed-off editorial choice.
3. **Save work before the session ends**. When changing code or reviewed
   data, open a *small* PR against current `main`. Merge only when its
   tests pass and any required editorial approval exists. For read-only
   research, write a short issue checkpoint with source URLs, hashes
   and evidence links; no empty PR is needed.
4. **Record an auditable checkpoint** using the compact format below:
   stage, result (`DONE`/`BLOCKED`), reviewed inputs, artifacts,
   PR/commit, exact successful tests, limitations and **next action**.
   A drafted PR or an in-progress CI run **does not** make a stage DONE.
5. **Update the issue's 7-item checklist and progress line**. Report to
   the user in **one short message**: `X/7 complete; current/next step;
   what passed; what remains; link`. Wait for their next request if they
   want to control the pacing, otherwise continue within available time
   without repeatedly demanding approval for routine technical choices.

Suggested checkpoint comment (keep the short form — links over log dumps):

```md
### Checkpoint 3/7 — DONE or BLOCKED
Input edition/revision: ...
Original/source SHA-256: ...
PR / merged commit: ...  (or read-only evidence)
Tests: <name and exact GitHub run URL; success/failure/not run>
Verified: ...
Unresolved / not tested: ...
Next (4/7, or retry 3/7): ...
```

If a conversation, connection or tool execution fails, the next session
**starts by reading the issue and linked GitHub artifacts** and resumes
the first unchecked stage. Work not pushed or logged is **not** counted.
Never restart an approved LSG release just because a new chat began.

## Size, safety and honest statuses

- **Seven stages, not seven giant PRs.** Prefer one reviewable PR
  addressing one concrete defect at a time, with its own tests. Multiple
  PRs may fit inside one stage. Avoid large, unmerged work branches.
- Every completed code checkpoint includes **focused tests and the
  repository validation suite** when applicable. Real-source private
  probes also need their exact official revision and test-run URL;
  passing generic synthetic tests is not a substitute.
- Keep **source content private** in diagnostic logs/artifacts if its
  license does not permit redistribution. Reports should expose counts,
  references and hashes, not wholesale publisher text.
- **`DONE`** means the specified gate passed with evidence. **`BLOCKED`**
  means one is missing or failed; **`NOT TESTED`** means not executed.
  **`N/A`** is allowed only for a genuinely inapplicable optional feature
  with justification. A green workflow does not imply editorial
  acceptance or actual external delivery.
- Do not implement a special exception to hide a discrepancy in the
  next Bible. Source-specific reviewed adaptations belong in explicit
  manifests and must be reversible.
- **Owner approval is reserved for editorially significant choices,
  rights decisions and publication**; ordinary programming, tests,
  issue updates and non-destructive research need no separate permission.
- Application-specific UI and installation behavior are **not**
  Bible Resources blockers. Record separate client issues when relevant.

## Completion

When 7/7 is *actually verified*, update the issue with the final release
link, module/catalogue hash evidence, distinct approval records, exact
successful workflow links, source/archive provenance, limitations and any
non-blocking follow-up issues, then close the per-Bible issue. **Issue #28**
is a separate, cross-edition generic-tooling project: it can remain open
even when a Bible is released, and must not be closed just because a
second-source diagnostic succeeded.
