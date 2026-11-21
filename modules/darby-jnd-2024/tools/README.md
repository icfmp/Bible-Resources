# Darby JND 2024 — source-pinned technical reader audit

The still-maintained command
[`probe_private_repaired_darby_sword.py`](probe_private_repaired_darby_sword.py)
is deliberately **edition-owned**. It reconstructs only the exact reviewed BPC
2024 source under a disposable working directory, applies the existing audited
technical overlays, and independently examines source/native SWORD text,
notes, versification, structured markers and representative reader behavior.
The original published Scripture and approved module payload are **never**
rewritten or uploaded by this command.

This command stays useful while its three separately triggered, real
source/reader evidence workflows remain active:

- [private native SWORD + Xiphos](../../../.github/workflows/darby-private-repaired-sword.yml)
- [pinned AndBible JSword](../../../.github/workflows/darby-andbible-jsword.yml)
- [private Android emulator](../../../.github/workflows/darby-andbible-android-private.yml)

They run from the repository root with `PYTHONPATH=scripts` and invoke the
module-local command directly. To verify the entrypoint without rebuilding
private source data, run:

```sh
PYTHONPATH=scripts python modules/darby-jnd-2024/tools/probe_private_repaired_darby_sword.py --help
``` The one required path adjustment compared with
its previous root-level location is locating the common
`config/osis-policy.json` relative to the repository root.

The shared OSIS/source guards, private readers, and XML repair helpers stay
under `scripts/`; only the **Darby-specific orchestration and source hashes**
are owned here. Keep the source/rights/editorial history in
[the existing edition record](../../../sources/cleaned/bibles/fr/darby-jnd-2024/editorial/README.md).
This is not a new importer, a new version or authorization to publish.
For new resources follow the
[canonical pipeline](../../../docs/PRODUCTION_PIPELINE.md).
