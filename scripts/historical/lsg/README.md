# Louis Segond historical research probes

## Synthetic versification probe

- Entrypoint: [`probe_lsg_v11n.py`](probe_lsg_v11n.py)
- Caller: [`lsg-v11n-probe.yml`](../../../.github/workflows/lsg-v11n-probe.yml)
- Regression test: [`test_lsg_v11n_probe.py`](../../../tests/test_lsg_v11n_probe.py)
- Input contract: [`lsg-v11n-probes.json`](../../../config/lsg-v11n-probes.json)

This is an **experimental historical** comparison of official SWORD NRSV/Segond verse-key slots using **synthetic text only**, not a real Bible converter or a release step. It has not been retired or deleted: its original behavior and review evidence remain reproducible, with the shared helper import root explicitly resolved from this nested directory. The old root script path has been removed instead of keeping a misleading compatibility wrapper. The workflow and tests now use this location.

Do not mistake source-key diagnostics for complete textual fidelity, verse restoration permission or a published module correction. For new source-first production use [the canonical procedure](../../../docs/PRODUCTION_PIPELINE.md).
