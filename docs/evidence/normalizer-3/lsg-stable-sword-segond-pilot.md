# Louis Segond 1910 — stock SWORD stable candidate (not released)

## Officially documented route

CrossWire [Alternate Versification](https://wiki.crosswire.org/Alternate_Versification)
recommends using a supported built-in versification for a conventional Bible,
passing the chosen system to `osis2mod -v`, and writing that exact
`Versification` to the SWORD module configuration. For an unsupported
system it says to **accept limitations** of the selected registry, use
GenBook where appropriate, or discuss a new versification upstream. It
explicitly states that out-of-grid source verses are appended to the
previous canonical verse **without an independent reference**.

Use **released SWORD** and the built-in `Segond` registry here. Do not
replace installed libsword, inject `v11n.xml`, claim Xiphos-specific support,
or make a private per-edition canonical index. Preserve original source
USFM/USFX and the unmodified verse milestones in the OSIS input.

## Real pilot

The text-free CI workflow `.github/workflows/lsg-stable-segond.yml`:
1. Acquires original eBible USFM/USFX with checksums and immutable source
   identity, and a checksum-pinned upstream USFM→OSIS converter.
2. Enforces reviewed CrossWire OSIS schema and structural policy.
3. Produces a **temporary, source-evidenced whitespace model** with the
   unchanged text of all 31,170 authored verse bodies. Authorial newline
   spacing is not asserted to be byte-identical.
4. Compiles that entire candidate with the stable installed
   `osis2mod -v Segond`, and reads all 1,189 original chapters using
   stock `diatheke`. Uses a normal `RawText` driver and standard
   SWORD `mods.d/` configuration.
5. Reports, *without publishing Bible text or binary*, every out-of-grid
   source verse, verified append to its preceding stable SWORD entry, and
   empty extra reader slot. A genuine missing/changed source character or
   unexpectedly populated slot **blocks** the diagnostic.
6. Never interprets a successful compile or continuous text agreement
   as an exact reference mapping, fully preserved notes, or release approval.

Expected (must be verified from the actual run, **not hardcoded**):
- eBible USFX has `Mark.10.53`; built-in `Segond` ends Mark 10 at
  verse 52. Stock `osis2mod` appends the text to reader Mark 10:52.
  **Mark 10:53 is not independently addressable in the stable module.**
- eBible source ends Job 34 at verse 36, but the stable registry has an
  unoccupied `Job.34.37` slot. This is not permission to invent a verse.

The **1910 printed transcription** on Wikisource also has Mark 10:53
and a *separate* Job 34:37:
- https://fr.wikisource.org/wiki/Bible_Segond_1910/%C3%89vangile_selon_Marc
- https://fr.wikisource.org/wiki/Bible_Segond_1910/Job
- https://ebible.org/study/content/texts/fraLSG/MK10.html

The source discrepancy at Job 34 may warrant an upstream eBible correction.
A print facsimile and publisher change history should be inspected before
any decision; no automated verse split or text relocation is authorized.

## Release and interoperability

**Updated editorial decision (2026-11-08):** the project owner explicitly
authorized grouping the original source verses 52 and 53 under stable SWORD
reader Mark 10:52, with every original Scripture character preserved and the
source archives untouched. This is a **reviewed, temporary index exception**,
not accidental corruption, a new versification, or a general license to merge
different Bible references. Machine-readable authorization:
`config/lsg-reviewed-verse-merges.json`. A generic source-bound readback
verifier checks the exact two source-to-reader keys and rejects any unreviewed
merge. Source-backed OSIS `n="52–53"` metadata is validated, but regular
SWORD frontends may ignore it; no fake text is inserted into Scripture.

The compromise **removes the categorical rejection of this known index
difference only**. A faithful full-binary notes/Strong/poetry/structure audit,
real reader validation, rights and final editorial review are still mandatory
before publication. PR #23's general release gate requires an explicit,
source- and binary-bound reviewed-merge provision to reflect this decision.

Before any distribution:
- Keep the owner's approved source→reader 52–53 merge strictly bounded to
  the recorded immutable source revision. No publisher/CrossWire outreach
  is required or authorized as a dependency. Avoid fake inline verse labels
  or claiming independent verse 53 access.
- Independently validate **all** compiled word/Strong, notes/cross-reference
  targets, poetry, titles, paragraphs and user-visible presentation.
- Demonstrate real standard-client interoperability, exact legal rights and
  reproducible hashes, complete a human review and run publication gates.
- Keep original source/converted candidate and SWORD module private until
  those criteria pass. Merely classifying the known limitation does not
  override the project's immutable-source and no-silent-versification rules.

Links: [PR #18](https://github.com/icfmp/Bible-Resources/pull/18),
[release gate PR #23](https://github.com/icfmp/Bible-Resources/pull/23),
[pilot issue #12](https://github.com/icfmp/Bible-Resources/issues/12).

## Verified stock-SWORD full-corpus checkpoint — 2026-11-08

- Workflow: https://github.com/icfmp/Bible-Resources/actions/runs/42525834984 (**success**)
- General `Validate`: https://github.com/icfmp/Bible-Resources/actions/runs/42525835034 (**success**)
- eBible USFM ZIP SHA-256: `64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900`
- eBible USFX ZIP SHA-256: `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`
- Original 66-book USFX: **31,170 authored verse keys / 1,189 chapters**; the independently validated, temporary OSIS model matches **31,170/31,170** authorial verse strings after source-evidenced display spacing. Original source bytes were not edited.
- **Released `osis2mod -v Segond` succeeded**, zero fatal/error diagnostics and **one outside-versification diagnostic**. Stock `diatheke` read all **1,189/1,189** chapters.
- **Exactly one source-only verse**: `Mark.10.53`. The complete original stream of 10:52+10:53 is found in stable SWORD's 10:52 entry; 10:53 cannot be queried independently.
- **Exactly one additional empty registry slot**: `Job.34.37`. It is not filled with invented Scripture.
- All **1,189/1,189** chapter character streams retain the source codepoints except separately identified display-only asterisks and whitespace, using the existing conservative reader classifier.
- The reader-only residual asterisk cases are `Ezra.4` (**4**), `Ezra.5` (**10**), and `Ezra.7` (**4**). These are explicitly logged visual differences, **not claimed to match source-authorial markup**.
- The workflow runs entirely on runner temporary data; uploads only text-free diagnostic JSON. **No Bible module, sources or publication generated.**

**Interpretation (superseded by the explicit owner decision):** the official
SWORD stable merge is now an *authorized* **temporary** deviation from exact
individual verse-key access, provided independent readback proves that every
source codepoint and annotation remains. This is not an approval of the
entire module. The compiled binary remains under review until full markup,
rights, edition and visual gate checks are complete. See
[upstream limitations](../../UPSTREAM_LIMITATIONS.md).
