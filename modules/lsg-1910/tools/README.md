# Segond 1910 — edition-only source and versification diagnostics

These scripts serve the **existing LSG 0.1.0 source/reader audit**. Their results can inform later editorial review, but they do not change the accepted module or create a release candidate.
They are not generic SWORD importers, publication tools, or authorization to
add missing Bible verses. Both remain read-only toward the original source
and the approved module. They use common helpers from `scripts/` rather
than copying them.

- [`lsg_sword_compare.py`](lsg_sword_compare.py) — compare authored eBible
  USFX against stock native SWORD chapter readback, distinguishing text,
  punctuation, whitespace, headings and annotation evidence. Run by
  [LSG fidelity CI](../../../.github/workflows/lsg-fidelity.yml); synthetic
  regression tests in [`test_lsg_sword_compare.py`](../../../tests/test_lsg_sword_compare.py).
- [`probe_lsg_v11n.py`](probe_lsg_v11n.py) — compile only **synthetic**
  verse placeholder cases under official `NRSV` and `Segond`
  versifications. No source text is recompiled or silently restored. Run by
  [LSG versification CI](../../../.github/workflows/lsg-v11n-probe.yml)
  using [the reviewed case configuration](../../../config/lsg-v11n-probes.json)
  and [`test_lsg_v11n_probe.py`](../../../tests/test_lsg_v11n_probe.py).

Run either command from the repository root with `--help` (for example, `python modules/lsg-1910/tools/probe_lsg_v11n.py --help`). The scripts
resolve `scripts/` for shared imports and `config/` from the repository
root; no root-level duplicate or compatibility stub remains.

The source/edition editorial decisions belong under the
[cleaned-source record](../../../sources/cleaned/bibles/fr/lsg-1910/editorial/README.md);
the signed/released payload and accompanying attestations remain unchanged.
Any future rebuilt version requires a separate complete original↔cleaned↔
native review and owner approval under the
[canonical pipeline](../../../docs/PRODUCTION_PIPELINE.md).
