# Historical Darby reader probes

These scripts reproduce **edition-specific** research against exact, privately prepared Darby 2024 candidates; they are not a generic import pipeline or publication authority.

## Final 0.1.1 Android UI probe

- [`probe_darby_011_final_android.py`](probe_darby_011_final_android.py) verifies exact private release-candidate identity before triggering bounded Android UI checks.
- [Private preflight workflow](../../../.github/workflows/darby-0.1.1-preflight.yml) now invokes the nested path.
- [Synthetic identity regression tests](../../../tests/test_probe_darby_011_final_android.py) import the moved module and still exercise SHA-locked fail-closed checks.

**Important:** a screenshot or Android import is not proof of textual integrity, source/OSIS parity, rights approval or publication. Reuse the [canonical source-first production process](../../../docs/PRODUCTION_PIPELINE.md) for future editions.

Historical code moved here without renaming the public resource, changing the selected source, SWORD binary, original commentary prose, or test fixtures.
