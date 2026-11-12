# Commentary onboarding — seven resumable checkpoints

**Scope:** commentaries (CrossWire SWORD RawCom/zCom or authorial OSIS/other
reviewed source), **not** Bible verse imports. Track each edition in one
`[Import]` issue. This specializes the evidence gates in
[Bible's seven-stage workflow](BIBLE_7_STAGE_WORKFLOW.md), while reusing
the existing ZIP preflight, bounded SWORD reader probes, generic OSIS guard,
strict `guard_commentary.py`, upstream/license policy and catalogue gates.

## Stages and durable evidence

| Step | Small independently reviewable evidence | Completion gate |
|---|---|---|
| **1/7. Select source and rights** | Exact *concise vs complete* edition identity, alternate witnesses, text/digital edits/annotations permissions and upstream .conf claim | Evidence-backed rights/edition review; unresolved rights block release |
| **2/7. Pin originals** | Original stock module ZIP and independently authored source, source URLs, SHA-256, sizes, unmodified .conf; repeatable retrieval | All used source editions independently identified and pinned; drift fails closed |
| **3/7. Original commentary audit** | Canonical book/intro/entry coverage, reference/range mapping, empty/duplicate keys, headings, paragraphs, lists, quotations, notes, hyperlinks and malformed markup | Full read-only source-native inventory, unknown structures classified |
| **4/7. SWORD integrity & source parity** | Complete entry/index readback, source-to-compiled words/punctuation/reference/markup comparison, original/built SHA; explain reuse or rebuild | No unexplained content/structure loss, guesses or fabricated reference mappings |
| **5/7. Editorial decisions** | Classified anomalies and source-bound, reviewed, reversible repair reports; preserve actual comments and quotations | Human editorial acceptance and recorded transformations; unapproved rewrites prohibited |
| **6/7. Independent readers** | Isolated ZIP installed in diatheke and tested in Xiphos and AndBible; intros, long/ranged entries, navigation and parallel rendering | Real logs/screenshots and per-client PASS / FAIL / NOT TESTED; no pretending a CLI test is GUI evidence |
| **7/7. Approve & publish** | Separate legal, editorial and technical approval, stable package SHA, licence/source profile, verified GitHub release, standard SWORD and JSON catalogue endpoints | All approval and publication states independently verified |

The existing strict OSIS validator applies **only when the actual original is
OSIS**. A compiled binary labelled `SourceType=OSIS` is *not itself*
its original authorial OSIS source. CCEL XML/ThML is an independent witness,
not interchangeable with an unverified Moody Press transcription. Never
reconstruct invented authorial source line numbers from a SWORD entry.

### Stage-4 internal slices (do not wait for one huge audit)

- **4a — keys and mapping:** book/chapter/verse and original commentary
  ranges; headings/intro slots, duplicate references and out-of-registry keys.
- **4b — complete content:** exact word/case/punctuation hashes for each
  entry, with separate quotes and note bodies; align independently to
  authenticated original, never just count characters.
- **4c — structure:** ordered opening/closing tags and positions of
  paragraphs, sections, titles, quotations, notes and references; isolate
  reader-only formatting differences.
- **4d — retain vs rebuild:** immutable inputs and evidence; prefer the
  stable original SWORD module when faithful. Never rewrite for cosmetics.

**Do not check 4/7 until all four slices have defensible evidence.**

## Reusable read-only observation (implemented)

Each candidate has a **separate reviewed manifest**
`config/commentary-intake/<resource-id>.json`; the initial file is
`mhcc-crosswire.json`. The Python intake has **no MHCC-specific content
logic**. It uses the existing HTTPS CrossWire provider allowlist, bounded
downloader, safe ZIP inspector, read-only `diatheke` scanner and content-free
sample SHA reports. No original bytes or the retrieved commentary text are
committed, copied to reports, or uploaded as workflow artifacts.

Run [Observe commentary intake (read-only)](
../.github/workflows/commentary-intake.yml) through Actions, or locally:

```sh
python scripts/commentary_intake.py --resource-id mhcc-crosswire \
  --stage 1 --report /tmp/mhcc-identity.json
python scripts/commentary_intake.py --resource-id mhcc-crosswire \
  --stage observe --report /tmp/mhcc-observation.json
```

- **Stage 1** uses no network and records that identity/rights need review.
- **`observe`** acquires the **current** CrossWire ZIP into disposable
  storage, verifies .conf module ID/version/language/license claim and ZIP
  safety, tests bounded diatheke entry retrieval, and writes only
  size, SHA-256, binary metadata and key-scoped hashes. It does **not**
  mean that 1/7, 2/7 or any subsequent stage has been accepted.
- After independent review, place the observed ZIP SHA-256 in that
  manifest and run **`--stage 2`** to enforce the exact pin on every
  redownload. A changed original **blocks** rather than repinning itself.
  Stage 2 still cannot be considered fully complete until the authorial
  witness is independently identified, compared and pinned.

The PR workflow selects **observe** when the archive SHA is still unpinned
and **stage 2** after the reviewed original ZIP SHA has been pinned; the
manual Action also accepts `auto`. The original is re-downloaded and hash-
checked, not silently reused from a previous CI runner. The workflow permits
stage 1/observe/2/auto for an arbitrary reviewed manifest. The PR workflow may fail on actual upstream drift, package
format or reader setup. Its green result is diagnostic **not a publication
gate**. Link the Actions run and permanent key facts in the resource issue,
without excerpting any source content into a log.

## First candidate: CrossWire MHCC (not MHC)

- [Official CrossWire MHCC record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC):
  concise **MHCC 2.0 (2021-02-14)**, English, public-domain distribution
  claim, declared Moody Press **28th printing**, ISBN **0-8024-5190-X**;
  predecessor electronic edition reportedly had approximately 1,200
  errors corrected. These corrections are part of the *specific digital
  witness* and must not be silently reversed.
- [CCEL concise commentary](https://www.ccel.org/ccel/henry/mhcc/mhcc)
  supplies a possible independent XML/text witness; its equivalence to
  the CrossWire/Moody edition **has not been demonstrated**.
- The prior [full MHC pilot](PILOT_SEGOND_MHC.md) is **not** this
  resource. In particular do not substitute CCEL's complete MHC or use
  the MHC 2.2 metadata for the concise module.

**Actual read-only observation (Action #43265980336, 2026-11-12):**
- CrossWire ZIP: 1,773,038 bytes; SHA-256
  `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d`,
  now pinned in the research manifest. Reacquisition against this pin is
  required, and does not by itself validate edition equivalence.
- Actual `mods.d/mhcc.conf`: `MHCC` / version 2.0 / `zCom` /
  `KJV` / `Lang=en` / `SourceType=OSIS`, declaring
  `DistributionLicense=Public Domain`. Conf SHA-256:
  `2762a04757ec3ee14bcf5d442fedcd47d2b938d573de4e9100a31aa073bc5863`.
- The actual `.conf` specifically credits
  `https://ccel.org/ccel/h/henry/mhcc/cache/mhcc.txt` as `TextSource`.
  Its identity, rights and full correspondence to the compiled SWORD data
  still need independent verification. CCEL's own
  [rights policy](https://www.ccel.org/about/copyright.html) warns that
  its editions may contain protected editorial material and says to ask
  permission for republication/commercial reuse.
- Bounded `diatheke` probes succeeded for several passages, but the
  19-byte response for John 3:16 is not credible evidence of a complete
  commentary entry; the generic intake flags such short readbacks for
  commentary entry/range mapping review. No missing-author-text claim.

**Outstanding:** independent source correspondence, full entry/range mapping
and text/structure parity, rights for digitization/corrections,
Xiphos/AndBible tests, reviewer sign-off and publication. The
initial research does **not** authorize a SWORD copy on the public Pages
repository.

See [import issue #177](https://github.com/icfmp/Bible-Resources/issues/177).
