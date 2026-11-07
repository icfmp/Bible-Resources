# Pilot 1: Louis Segond 1910 (eBible) and Matthew Henry Complete (CrossWire)

**Tracking:** [issue #12](https://github.com/icfmp/Bible-Resources/issues/12).

**Status as of 2026-11-07:** candidates, license declarations and **online
layout reference examples** reviewed; source archives and compiled SWORD
modules **not yet downloaded, checked, transformed, or published**. This
document is a reproducible pilot protocol, **not a completed trial**.

## Source selection and rights

| Resource | Selected for pilot | Evidence | Caution |
|---|---|---|---|
| Segond 1910 | eBible \`fraLSG1910eb\`, source \`fraLSG\` | [eBible details with SWORD, USFM/USFX, OSIS and public-domain declaration](https://ebible.org/find/details.php?all=1&id=fraLSG) | Verify actual SWORD \`.conf\` and individual file rights; do not infer SWORD v11n from title |
| Matthew Henry **complete** | CrossWire \`MHC\` version **2.2**, \`zCom4\` | [CrossWire official listing](https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC) | **Not** concise \`MHCC\`. Check original \`.conf\`, CCEL correspondence and rights before publishing |

**Important upstream exception:** CrossWire also hosts \`FreSegond1910\`,
version **4.0**, enhanced with Strong's numbers, declared
\`Copyrighted; Permission to distribute granted to CrossWire\`. The
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
SWORD module lacks those boundaries; actual \`diatheke\` / OSIS export
inspection is still needed.

**Pilot check:** verify boundaries, authorial headings, nested sections,
entry ranges (\`annotateRef\`), KJV scripture blocks and embedded Bible
citations. Preserve all quotations. We may tag clearly identified
introductory Scripture quotations for **optional UI folding** only after
validating OSIS conventions and verifying boundaries. Never remove a
quotation that Henry uses in his argument.

## Versification and omitted verses

Official SWORD v11n data, **not one mapping per translation**:
[VERSIFICATION_POLICY.md](VERSIFICATION_POLICY.md).

- Confirm *actual* \`Versification\` value in each downloaded module's
  \`mods.d/*.conf\` (CrossWire lists MHC as KJV in several source records,
  but we must verify its actual packaged config).
- Verify the installed SWORD engine supports each value. The official
  registry includes French \`Segond\` and English \`KJV\`; this does not
  imply that every Segond module declares \`Segond\`.
- Run \`emptyvss\` and audit any missing slots. Distinguish actual
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
   \`diatheke\` output for Psalm 23, Psalm 119, Genesis 1 and a long
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

- The official OSIS 2.1.1 XSD is not yet SHA-256-pinned and reviewed;
  \`guard_osis.py\` intentionally blocks real processing.
- The deterministic SWORD importer / content-normalizer, authoritative
  round-trip checker and actual GTK visual comparison harness are not
  implemented.
- This project has not yet retrieved and executed the two original
  full modules. Online excerpts are presentation references only.
- GitHub Pages needs explicit repository-side activation before any
  public catalogue publication.

No passing unit test on synthetic fixtures can replace the **real
cross-client SWORD verification** required for these two modules.

## Prepared first-pass commands (no content modifications)

The tested *preparation* lives in these scripts:

- \`config/pilot-sources.json\`: the two exact allowlisted module IDs and
  HTTPS upstream ZIP URLs, plus test passage keys.
- \`scripts/pilot_fetch.py\`: HTTPS-only streaming source download with a
  file-size limit and redirect allowlist into a private temporary directory;
  refuses overwriting existing data.
- \`scripts/pilot_preflight.py\`: checks ZIP safety, module identity/driver,
  .conf metadata, SHA-256 and sizes **without extracting text**. If a step
  fails, the JSON result is marked blocked rather than recycling a success.
- \`scripts/pilot_runtime.py\`: re-checks ZIP structure, unpacks only
  preflighted members to a disposable workspace, and calls real
  \`diatheke\` on the registered example keys. It records result presence
  and hashes, **not the returned passage text**.
- \`scripts/probe_official_osis.py\`: checks the real CrossWire schema
  location, digest, imports/includes and offline XMLSchema compilation.
  It **does not** silently set \`schema_status=reviewed\`.

The workflow \`.github/workflows/pilot-preflight.yml\` is
**manual only**. To start LSG deliberately, go to GitHub Actions →
**Pilot source preflight (on demand, read-only)** → Run workflow →
\`pilot=lsg\`. It will fetch the exact eBible SWORD and USFM ZIPs to
the runner's temporary directory, inspect both, read sample SWORD verses,
and attach **only JSON diagnostics**; never a distributable Bible package.
Choose \`pilot=mhc\` separately when the MHC turn begins.

A local equivalent after installing \`diatheke\` is:

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
verses, notes, formatting and commentary entries, OSIS XSD pinning,
display before/after, correction decisions, SWORD recompilation and
approval will take place during the pilot itself. The first pilot must
not be declared normalized merely because this metadata preflight passes.
