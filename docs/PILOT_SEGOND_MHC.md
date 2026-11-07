# Pilot 1: Louis Segond 1910 (eBible) and Matthew Henry Complete (CrossWire)

**Tracking:** [issue #12](https://github.com/icfmp/Bible-Resources/issues/12).

**Status as of 2026-11-07:** preparation scripts and manual read-only pilot
workflow implemented; official CrossWire/W3C XSD pair verified and pinned;
source archives and compiled SWORD modules **not yet fetched, compared,
normalized, or published**. This
document is a reproducible pilot protocol, **not a completed trial**.

## Source selection and rights

| Resource | Selected for pilot | Evidence | Caution |
|---|---|---|---|
| Segond 1910 | eBible `fraLSG1910eb`, source `fraLSG` | [eBible details with SWORD, USFM/USFX, OSIS and public-domain declaration](https://ebible.org/find/details.php?all=1&id=fraLSG) | Verify actual SWORD `.conf` and individual file rights; do not infer SWORD v11n from title |
| Matthew Henry **complete** | CrossWire `MHC` version **2.2**, `zCom4` | [CrossWire official listing](https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC) | **Not** concise `MHCC`. Check original `.conf`, CCEL correspondence and rights before publishing |

**Important upstream exception:** CrossWire also hosts `FreSegond1910`,
version **4.0**, enhanced with Strong's numbers, declared
`Copyrighted; Permission to distribute granted to CrossWire`. The
underlying historical text may be public domain, but the **module as packaged
and annotated is not automatically ours to redistribute or alter**.
Do not bypass the five-source priority policy: record the CrossWire
candidate, its feature/rights differences and why it cannot currently be
republished, then use the separately licensed eBible edition **without
claiming the modules are verified identical**.
Source: https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=FreSegond1910

The eBible catalog itself also offers downloadable OSIS/USFM source and
PDF output, so source-level fidelity comparison is possible once bytes
are retrieved. Record the precise edition and updates, not just "Louis
Segond"; eBible's page displayed a source update on **2026-10-30**.
Metadata alone cannot prove identity with a particular printed edition.

## First online presentation observations (not source-file verification)

### Segond: Psalm 23

**Read-only HTML reference:**
https://ebible.org/fraLSG/PSA023.htm

The published layout distinguishes the superscription *Cantique de David*
from the psalm body, and prints multiple poetic lines within the same verse.
In particular, verse 2 has two visual lines, verse 3 has three, and verse 6
has several. The end of a poetic line is **not** necessarily the end of a
verse or the start of a separate paragraph.

**Pilot check:** compare this actual reference layout to the OSIS/USFM
source and SWORD extracted markup, then to Bible GTK rendering. Avoid
collapsing lines into prose or adding full paragraph spacing between
each line. If the source is correct and the GTK renderer is wrong, fix
**Bible**, not the SWORD text. Audit Psalm 119 separately for longer
repeating stanzas.

### MHC: Genesis introduction and Genesis 1

**Read-only editorial reference:**
https://www.ccel.org/ccel/henry/mhc1.Gen.i.html

CrossWire explicitly credits CCEL for the full commentary. In CCEL's
Genesis introduction, the text is divided into successive paragraphs,
rather than a single giant paragraph. This gives us a preliminary reference
for restoring **lost** paragraph boundaries if the corresponding SWORD
entry has flattened them. This observation alone is *not* proof that the
SWORD module lacks those boundaries; actual `diatheke` / OSIS export
inspection is still needed.

**Pilot check:** verify boundaries, authorial headings, nested sections,
entry ranges (`annotateRef`), KJV scripture blocks and embedded Bible
citations. Preserve all quotations. We may tag clearly identified
introductory Scripture quotations for **optional UI folding** only after
validating OSIS conventions and verifying boundaries. Never remove a
quotation that Henry uses in his argument.

## Versification and omitted verses

Official SWORD v11n data, **not one mapping per translation**:
[VERSIFICATION_POLICY.md](VERSIFICATION_POLICY.md).

- Confirm *actual* `Versification` value in each downloaded module's
  `mods.d/*.conf` (CrossWire lists MHC as KJV in several source records,
  but we must verify its actual packaged config).
- Verify the installed SWORD engine supports each value. The official
  registry includes French `Segond` and English `KJV`; this does not
  imply that every Segond module declares `Segond`.
- Run `emptyvss` and audit any missing slots. Distinguish actual
  deliberate text-critical omissions from different numbering and
  accidental import errors.
- For a confirmed omission **within its existing v11n**, keep the empty
  verse and an **editorial note backed by that edition's source**. Do not
  import an omitted verse from a different Bible. Verify how SWORD and
  Bible display empty *verse 1* without substituting dummy Scripture.
- Test MHC commentaries for whole-chapter ranges and correct
  correspondence to the Bible even if their versifications differ.

Suggested **audit references**, not assertions that this Segond edition
omits them: John 5:4, Matthew 18:11, Acts 8:37, and Mark 16:9–20.
The source edition decides the reading; **we do not edit its textual
decisions in this pilot**.

## Minimum acceptance report

For both modules, publish a **review report**, not copyrighted/unapproved
third-party binaries, with:

1. Exact SWORD .conf / source format, original provider, version,
   source URL, rights/derivative permissions, SHA-256 of original source
   and any compiled module.
2. SWORD detected v11n, full set of source verse or commentary entry
   keys, empty/out-of-v11n counts, and missing-source distinctions.
3. Diff of full source text and markup before/after; separate typography,
   verse-key, editorial note, Strong/morph, and annotation checks.
4. Representative before/after visual evidence in **Bible GTK** and
   `diatheke` output for Psalm 23, Psalm 119, Genesis 1 and a long
   MHC chapter/section.
5. Every automatic transformation rule with its official format
   justification, original-source path and line or SWORD verse/entry key,
   and corresponding regression fixture. Unknown cases abort.
6. Reviewed whether a third-party PDF or CCEL edition matches the text;
   source pages or URLs and explicitly marked faithful restoration
   versus reader-optimized adaptation.
7. **Clarity over abundance:** if a case is not covered by current
   rules, the assistant reviews it and proposes a standards-compliant
   correction. If no safe and lawful correction exists, **exclude the
   resource** rather than presenting it as normalized.

## Who is responsible?

- **Assistant (Bible Resources developer):** own source acquisition,
  fingerprinting, normalizer, source-to-binary checks, generic tests, real
  SWORD reader verification, source comparison and editorial diagnosis.
  Maintain the technical and editorial change log; report any blocked case.
- **Codex:** independent audit and targeted support when a technical task
  cannot be completed safely by the assistant; not the default executor.
- **Simon:** choose scope and approve material editorial adaptations.

## Current technical blockers

- The official CrossWire OSIS 2.1.1 XSD and its W3C xml.xsd import
  are now reviewed, pinned, and compiled offline. Real module content
  has **not yet** passed the OSIS source gate.
- The deterministic SWORD importer / content-normalizer, authoritative
  round-trip checker and actual GTK visual comparison harness are not
  implemented.
- The manual preflight can fetch and check original modules on request,
  but **the LSG/MHC module ZIPs have not yet been run through it**.
  Online excerpts remain presentation references only.
- GitHub Pages needs explicit repository-side activation before any
  public catalogue publication.

No passing unit test on synthetic fixtures can replace the **real
cross-client SWORD verification** required for these two modules.

## Prepared first-pass commands (no content modifications)

The tested *preparation* lives in these scripts:

- `config/pilot-sources.json`: the two exact allowlisted module IDs and
  HTTPS upstream ZIP URLs, plus test passage keys.
- `scripts/pilot_fetch.py`: HTTPS-only streaming source download with a
  file-size limit and redirect allowlist into a private temporary directory;
  refuses overwriting existing data.
- `scripts/pilot_preflight.py`: checks ZIP safety, module identity/driver,
  .conf metadata, SHA-256 and sizes **without extracting text**. If a step
  fails, the JSON result is marked blocked rather than recycling a success.
- `scripts/pilot_runtime.py`: re-checks ZIP structure, unpacks only
  preflighted members to a disposable workspace, and calls real
  `diatheke` on the registered example keys. It records result presence
  and hashes, **not the returned passage text**.
- `scripts/probe_official_osis.py`: checks the real CrossWire schema
  location, digest, imports/includes and offline XMLSchema compilation.
  It **does not** silently set `schema_status=reviewed`.

The workflow `.github/workflows/pilot-preflight.yml` is
**manual only**. To start LSG deliberately, go to GitHub Actions →
**Pilot source preflight (on demand, read-only)** → Run workflow →
`pilot=lsg`. It will fetch the exact eBible SWORD and USFM ZIPs to
the runner's temporary directory, inspect both, read sample SWORD verses,
and attach **only JSON diagnostics**; never a distributable Bible package.
Choose `pilot=mhc` separately when the MHC turn begins.

A local equivalent after installing `diatheke` is:

    python scripts/pilot_fetch.py --pilot lsg --directory /tmp/bible-pilot
    python scripts/pilot_preflight.py --pilot lsg \
      --sword-zip /tmp/bible-pilot/sword.zip \
      --authored-zip /tmp/bible-pilot/authored.zip \
      --report reports/pilot-preflight.json
    python scripts/pilot_runtime.py --pilot lsg \
      --sword-zip /tmp/bible-pilot/sword.zip \
      --report reports/pilot-reader.json

These are **inspection and runtime-preflight tools**, not an
editorial/source fidelity test. The actual comparison of all source
verses, notes, formatting and commentary entries, OSIS source validation,
display before/after, correction decisions, SWORD recompilation and
approval will take place during the pilot itself. The first pilot must
not be declared normalized merely because this metadata preflight passes.

## Baseline source fingerprints (read-only, 2026-11-07)

[Original SWORD/USFM source evidence](evidence/normalizer-3/real-pilot-source-signals.json)
was gathered from the real eBible `fraLSG1910eb` SWORD and USFM ZIPs and
the actual CrossWire full `MHC` ZIP in GitHub Actions. Requests now put
the SWORD `-k` key **last**, with bounded output and timeout: earlier
unbounded-key reports were **invalid** and must not be reused. The LSG
module actually declares `Versification=NRSV` (`zText`, version `100.0`),
and the MHC module declares `Versification=KJV` (`zCom4`, version `2.2`).
LSG Psalm 23/119 entries contain poetry-line signals; MHC Genesis
entries contain paragraph signals. **This is not** an all-verses text
comparison, MHC authored XML inspection or actual candidate normalization.
No source or compiled module was changed.


## LSG full-authoring / SWORD trial — 7 November 2026

The live [PR #16](https://github.com/icfmp/Bible-Resources/pull/16) was
**merged** after a successful real run with 165 Python tests and a separate
source-to-compiled comparison of all 1,189 chapters. eBible's genuine
public-domain `fraLSG` USFM and USFX archives contain the same 31,170
verse references, in the same 66-book order. The original compiled
`fraLSG1910eb` SWORD module (v100.0, `zText`) instead declares
`Versification=NRSV` and exposes 31,104 verse keys in `diatheke`
chapter output. The audit lists **112 original-only** and **46
SWORD-only** keys. These are *reference-index mismatches*, not a
conclusion that any original Scripture content should be removed.

After comparing continuous Scripture text per book with NFC and whitespace
normalization (without silently dropping original punctuation),
**65/66 books** have equal text checksums. Ezra is the remaining exception;
some of its discrepancies are diatheke asterisk-emphasis wrappers, and
others still require source-by-source review. Matching entire books do not
prove correct **verse boundaries**: examples include Exod 7.26–29 being
appended to the output of Exod 7.25. CrossWire documents that `osis2mod`
may append verses outside the selected canonical scheme to the last
accepted entry, losing their individual references. This behavior is
NOT a textual criticism decision or an intentional omitted verse.

CrossWire publishes an official `Segond` versification for French
Louis Segond 1910. It is an explicit **candidate** for rebuilding the
index; never change only `mods.d/*.conf` without rebuilding and
confirming every verse boundary, note and reference. The separate
synthetic-source-key compiler check in PR #17 compares actual
`osis2mod -v NRSV` and `-v Segond` behavior but is not a publication.

**Source formats:** USFM and USFX are verified and inspected; the
publisher's older advertised `fraLSG_osis.zip` endpoint currently returns
HTTP 404. USFX is not OSIS and cannot be fed directly to the CrossWire
OSIS XSD. An exact, rights-cleared and auditable USFM/USFX → OSIS
conversion will be needed if no genuine matching OSIS source is
recoverable. The real SWORD module's translation notes, cross references,
word markup and Bible GTK visual presentation have **not** yet been
verified after a rebuild. No real Scripture was edited or published.

The complete actual trial artifacts, including reference counts and
private text-free hashes, are retained with the successful
[LSG authored-source fidelity workflow](https://github.com/icfmp/Bible-Resources/actions/runs/42365912858).
