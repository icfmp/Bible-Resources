# MHCC — original CrossWire source reader research

These commands are **edition-specific private evidence**, not generic Bible
imports, OSIS converters or a second publication pipeline. They inspect the
exact original CrossWire **MHCC 2.0** `zCom` witness pinned by
[`config/commentary-intake/mhcc-crosswire.json`](../../../config/commentary-intake/mhcc-crosswire.json).
The current approved module is `modules/mhcc-crosswire/` version 0.1.1.
Preserve the distinction between the upstream original and any reviewed
corrected/rebuilt candidate.

- [`commentary_private_candidate_xiphos_gui.py`](commentary_private_candidate_xiphos_gui.py):
  in a disposable isolated real Xiphos, compare five *actual* selected
  passages and source links from an exact byte-identical private repackage,
  alongside the independently attested published LSG Bible. The private ID
  `BRMHCCReview` is research-only. Invoked by
  [private Xiphos acceptance CI](../../../.github/workflows/commentary-private-candidate-xiphos-gui.yml).
- [`commentary_stock_andbible_android.py`](commentary_stock_andbible_android.py):
  attempt official stable AndBible Android import of the unchanged pinned
  original stock ZIP in a disposable emulator, observing actual UI controls.
  A screenshot, successful click or imported package **does not** establish
  text/link correctness. Invoked by
  [original stock Android CI](../../../.github/workflows/commentary-zcom-andbible-android.yml).

From repository root, a safe command-only check is:

```sh
PYTHONPATH=scripts python modules/mhcc-crosswire/tools/commentary_private_candidate_xiphos_gui.py --help
PYTHONPATH=scripts python modules/mhcc-crosswire/tools/commentary_stock_andbible_android.py --help
```

Both sources were moved **byte-identically** from the shared `scripts/` root,
their actual CI commands and test import roots updated without compatibility
wrappers. The reusable source/XML, SWORD index, Xiphos and Android helpers
remain under `scripts/`.

Historical editor decisions and unresolved questions belong with the
[cleaned MHCC source record](../../../sources/cleaned/commentaries/en/mhcc-crosswire/editorial/README.md).
Original source, approved module, edition/text/notes, release assets and rights
are not modified by this research tool layout. Future changes must follow
[the common production process](../../../docs/PRODUCTION_PIPELINE.md).
