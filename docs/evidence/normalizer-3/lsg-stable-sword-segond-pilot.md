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

This **stable SWORD pilot is intentionally not yet a publishable module**.
The stock binary follows official behavior but cannot preserve the
authorial Mark 10:53 address. That is an explicitly recorded loss of index
fidelity, not lost continuous Scripture text. It remains blocked by the
strict independent-reference publication gate in PR #23.

Before any distribution:
- Decide the editorial treatment of the inaccessible reference with the
  publisher/CrossWire and obtain explicit approval; do not insert a visible
  fake reference or claim an independent verse 53.
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
