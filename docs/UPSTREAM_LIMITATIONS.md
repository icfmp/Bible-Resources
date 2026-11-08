# Upstream limitations register

This is an **internal Bible Resources maintenance log**, not a request to
contribute to CrossWire or eBible. The project owner chose to proceed
independently with a temporary, explicit, source-faithful text merge rather
than wait for an upstream change. Do not send automatic emails or open
third-party tickets based on this file.

Every item must have: source/edition, observed behavior, evidence, impact,
temporary workaround and a clear condition for future reconsideration.
Never silently patch publisher USFM, verse IDs or the installed SWORD canon.

| ID | Upstream component | Observable problem | Status |
| --- | --- | --- | --- |
| UP-001 | SWORD stock Segond v11n | Index does not include Mark 10:53 | Workaround explicitly authorized; separate verse 53 key unavailable |
| UP-002 | SWORD versioned XML versification / JSword | Source-derived custom XML-v11n not portable to stable SWORD 1.9/JSword | Deferred; no dependency on future release |
| UP-003 | eBible `fraLSG` USFM/USFX | Job 34 ends with 36 although printed 1910 transcription identifies separate 37 | Investigate facsimile; source left unchanged |
| UP-004 | `osis2mod` and frontends | OSIS verse `n` editorial label generally not retained by stock importer, so 52–53 cannot be guaranteed as an on-screen verse number | Try metadata-only label, verify actual reader; never fake Scripture words |

## UP-001 — Marc 10.53 in stable SWORD Segond

- Source: eBible `fraLSG` USFM/USFX snapshots, ZIP SHA-256
  `64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900`
  and `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`.
- Stock registry: `Segond` has Mark 10:52 as last canonical verse.
  1910 edition and eBible source identify distinct 10:53.
- Observed: official `osis2mod -v Segond` appends original 10:53 body
  directly after 10:52; SWORD can read all original chapter characters
  but cannot navigate separately to source verse 53.
- Evidence: [complete stable readback](https://github.com/icfmp/Bible-Resources/actions/runs/42526118948),
  [full v11n inventory](lsg-sword-v11n-full-coverage.md).
- Compromise **explicitly approved by the project owner, 2026-11-08**:
  one compiled entry 10:52 containing *both entire source verse bodies,
  in order*. Keep all source archives, USFM/USFX keys and original OSIS
  milestones untouched. In the prepared OSIS clone alone, attempt
  `n="52–53"` as editorial metadata; CrossWire normally removes verse
  tags, so no claim that every frontend shows this label.
- Machine-readable authorization (source SHA and source→reader IDs):
  `config/lsg-reviewed-verse-merges.json`. The generic checker must
  confirm the exact observed append **and full chapter character
  preservation**, with no other unreviewed source-only references.
- No attempt to edit the installed `Segond` table or create a private canon.
- Revisit when a broadly deployed version of SWORD and JSword supports
  independent source-referenced Mark 10:53, and only after full QA.

## UP-002 — Experimental XML-versification availability

- The experimental SWORD HEAD XML v11n prototype can represent all current
  eBible 31,170 authored reference identifiers, but stock SWORD 1.9
  cannot read every key; JSword compatibility is not established.
- No automatic upgrades, no bundled custom libsword and no unverified
  packaging dependencies. Remain on official stable SWORD.
- Evidence: [experimental protocol](lsg-sword-v11n-full-coverage.md).
- Revisit on an independently available compatible stable release, with
  actual target frontend testing.

## UP-003 — Job 34:37 boundary of digitized edition

- The eBible source provides only verse 36 at Job 34's end,
  whereas a 1910 print transcription has 36 and 37 separately.
- This is a **candidate** source-digitization inconsistency, not verified
  corruption or permission to insert/reassign content.
- Retain publisher original verse 36 unchanged and leave stable
  `Job.34.37` slot empty; do not fabricate verse 37 or move text.
- Revisit after comparing a verified 1910 printed page image, editor notes
  and the authoritative eBible source revision.
- Evidence: https://fr.wikisource.org/wiki/Bible_Segond_1910/Job ,
  https://ebible.org/fraLSG/copyright.htm .

## UP-004 — Display of a merged-verse number

- OSIS `verse@n` is an editorial attribute, but `osis2mod` ordinarily
  strips verse tags from the compiled module, while clients show
  the canonical reader index. The preferred `52–53` may therefore not
  be visible to readers even when present in the source candidate.
- The project explicitly prefers **no invented visible Bible words** to
  an apparent correction that would alter source text. A clear module
  introduction/editorial notice or application metadata can explain
  grouped verses; neither is falsely claimed to be the canonical number.
- Revisit on verified support for alternative display labels from
  source metadata in standard readers.

## Separate release requirements

The authorization of UP-001 **does not** waive the remaining checks:
compare all compiled notes/targets, Strong tags, poetry, paragraphs,
punctuation and headings to originals; verify real client display, exact
rights, human editorial sign-off, original source archive integrity,
reproducibility and distribution readiness. The temporary index merge is
an **exception to reference access only**, never to Bible text fidelity.
