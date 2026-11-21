# Shared BSI regression tests

Test the [shared scripts](../scripts/) without mutating the immutable
ACAI/source input:

```bash
python3 -I bible-semantic-index/tests/test_workspace_layout.py
python3 -I bible-semantic-index/tests/test_build.py
python3 -I bible-semantic-index/tests/test_resolve.py
python3 -I bible-semantic-index/tests/test_distribution_profile.py
python3 -I bible-semantic-index/tests/test_audit_person_overlaps.py
```

These tests run in [the BSI GitHub Actions workflow](
../../.github/workflows/entity-index.yml). Pinned UBS Greek/Hebrew
dictionary tests remain beside their own pipelines and are run separately.
