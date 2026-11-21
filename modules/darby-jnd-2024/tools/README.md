# Darby JND 2024 — edition-owned QA replay

These two tools are **not** the shared Bible ingestion/publishing pipeline.
They reconstruct and inspect only the exact, previously reviewed **Darby 0.1.1
private candidate** (source IDs, ZIP digests, original-note counts and module
metadata are deliberately pinned). They remain runnable as regression/evidence
tools for the existing [private candidate preflight](../../../.github/workflows/darby-0.1.1-preflight.yml),
which invokes them with `PYTHONPATH=scripts` from the repository root.

- [`prepare_darby_011_private_release_candidate.py`](prepare_darby_011_private_release_candidate.py):
  verify the already-attested source/native receipt, then prepare only a
  disposable 0.1.1 SWORD ZIP and metadata report. Never publish it.
- [`probe_darby_011_final_android.py`](probe_darby_011_final_android.py):
  verify a strictly pinned **private** 0.1.1 candidate before installing
  it in a disposable AndBible emulator for read-only visual evidence.
  A screenshot or successful launch is **not** editorial acceptance.

The scripts' source was moved **byte for byte**, with the direct test
imports and CI commands changed to point here. They do not rewrite
`sources/original/`, `sources/cleaned/`, `modules/*/payload/`,
the release catalogue or any authorial text. The original reviewed decision
and full provenance belong in [the edition's editorial notes](../EDITORIAL.md)
and [its cleaned-source record](../../../sources/cleaned/bibles/fr/darby-jnd-2024/editorial/README.md).

For a new edition or a different translation, use the
[shared production pipeline](../../../docs/PRODUCTION_PIPELINE.md). Do **not**
reuse or generalize the pinned version numbers/hashes by string replacement.
Retire these replay scripts once their last real caller and replay obligation
have been explicitly checked under [tooling issue #430](https://github.com/icfmp/Bible-Resources/issues/430).
