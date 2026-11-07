"""Offline tests: version comparison and non-destructive upstream monitoring."""
import io
from pathlib import Path
import sys
import tarfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_updates import archive_catalog, check, compare_link, parse_conf, version_cmp


class UpdateTests(unittest.TestCase):
    def test_numeric_version_order(self):
        self.assertEqual(version_cmp("1.2.10", "1.2.9"), 1)
        self.assertEqual(version_cmp("1.0", "1.0.0"), 0)
        self.assertEqual(version_cmp("2.0", "2.1"), -1)
        self.assertIsNone(version_cmp("2.0-beta", "2.0"))

    def test_repeated_conf_fields(self):
        c = parse_conf(b"[KJV]\nVersion=2.1\nHistory_2.0=Old\nHistory_2.1=New\n")
        self.assertEqual(c["module_id"], "KJV")
        self.assertEqual(c["version"], "2.1")
        self.assertEqual(len(c["conf_sha256"]), 64)

    def test_safe_archive_reader(self):
        f = io.BytesIO()
        with tarfile.open(fileobj=f, mode="w:gz") as t:
            content = b"[KJV]\nVersion=3.0\n"
            good = tarfile.TarInfo("mods.d/kjv.conf")
            good.size = len(content)
            t.addfile(good, io.BytesIO(content))
            bad = tarfile.TarInfo("../../escape")
            bad.size = 1
            t.addfile(bad, io.BytesIO(b"x"))
        d = archive_catalog(f.getvalue())
        self.assertEqual(list(d), ["kjv"])
        self.assertEqual(d["kjv"]["version"], "3.0")

    def test_detect_new_version_and_same_version_change(self):
        base = {"last_integrated_version": "1.1", "last_integrated_conf_sha256": "a" * 64}
        self.assertEqual(compare_link(base, {"version": "1.2", "conf_sha256": "b" * 64}), "upstream_update_available")
        self.assertEqual(compare_link(base, {"version": "1.1", "conf_sha256": "b" * 64}), "upstream_metadata_changed")
        self.assertEqual(compare_link(base, None), "missing_upstream")

    def test_our_accepted_fix_returning_upstream_is_not_a_new_update(self):
        link = {"last_integrated_version": "1.0",
                "contributions": [{"url": "https://example.org/pull/4",
                                   "state": "accepted", "patch_sha256": "a" * 64}],
                "reconciliations": [{
                    "upstream_version": "1.1", "upstream_conf_sha256": "b" * 64,
                    "upstream_content_sha256": "c" * 64,
                    "curated_content_sha256": "d" * 64,
                    "result": "equivalent_to_curated",
                    "contribution_url": "https://example.org/pull/4",
                    "evidence_url": "https://example.org/comparison/1.1",
                    "reviewed_by": "editor"}]}
        remote = {"version": "1.1", "conf_sha256": "b" * 64}
        self.assertEqual(compare_link(link, remote), "our_contribution_returned_upstream")
        # A later release or different conf cannot piggyback on the prior review.
        self.assertEqual(compare_link(link, {"version": "1.2", "conf_sha256": "e" * 64}),
                         "upstream_update_available")
        self.assertEqual(compare_link(link, {"version": "1.1", "conf_sha256": "e" * 64}),
                         "upstream_update_available")

    def test_accepted_pr_does_not_prove_a_released_source_is_equivalent(self):
        link = {"last_integrated_version": "1.0",
                "contributions": [{"url": "https://example.org/pull/4", "state": "accepted",
                                   "patch_sha256": "a" * 64}]}
        self.assertEqual(compare_link(link, {"version": "1.1", "conf_sha256": "b" * 64}),
                         "upstream_update_available")

    def test_upstream_includes_our_fix_but_other_changes_still_require_review(self):
        link = {"last_integrated_version": "1.0",
                "contributions": [{"url": "https://example.org/pull/4", "state": "released",
                                   "patch_sha256": "a" * 64}],
                "reconciliations": [{
                    "upstream_version": "1.1", "upstream_conf_sha256": "b" * 64,
                    "upstream_content_sha256": "c" * 64,
                    "curated_content_sha256": "d" * 64,
                    "result": "contains_other_changes",
                    "contribution_url": "https://example.org/pull/4",
                    "evidence_url": "https://example.org/review",
                    "reviewed_by": "editor"}]}
        self.assertEqual(compare_link(link, {"version": "1.1", "conf_sha256": "b" * 64}),
                         "upstream_update_available")

    def test_report_marks_self_contribution_candidate_without_claiming_match(self):
        provider = {"id": "crosswire", "enabled": True, "base_url": "https://example.test/"}
        link = {"provider": "crosswire", "module_id": "KJV",
                "last_integrated_version": "1.0",
                "contributions": [{"url": "https://example.org/pull/4", "state": "accepted",
                                   "patch_sha256": "a" * 64}]}
        manifest = {"id": "kjv", "sword_id": "KJV", "version": "1.0.0",
                    "upstreams": [link]}
        report = check([provider], [manifest], {}, fetch_catalog=lambda _: {},
                       fetch_conf=lambda *_: {"version": "1.1", "conf_sha256": "b" * 64})
        row = report["modules"][0]["upstreams"][0]
        self.assertEqual(row["status"], "upstream_update_available")
        self.assertTrue(row["possible_return_of_our_contribution"])
        self.assertTrue(row["review_required"])
        self.assertEqual(row["our_contributions"][0]["state"], "accepted")

    def test_report_marks_exact_reviewed_equivalence_and_provenance(self):
        provider = {"id": "crosswire", "enabled": True, "base_url": "https://example.test/"}
        link = {"provider": "crosswire", "module_id": "KJV",
                "last_integrated_version": "1.0",
                "contributions": [{"url": "https://example.org/pull/4", "state": "released",
                                   "patch_sha256": "a" * 64}],
                "reconciliations": [{
                    "upstream_version": "1.1", "upstream_conf_sha256": "b" * 64,
                    "upstream_content_sha256": "c" * 64,
                    "curated_content_sha256": "d" * 64,
                    "result": "equivalent_to_curated",
                    "contribution_url": "https://example.org/pull/4",
                    "evidence_url": "https://example.org/full-diff",
                    "reviewed_by": "editor"}]}
        manifest = {"id": "kjv", "sword_id": "KJV", "version": "1.0.0",
                    "upstreams": [link]}
        report = check([provider], [manifest], {}, fetch_catalog=lambda _: {},
                       fetch_conf=lambda *_: {"version": "1.1", "conf_sha256": "b" * 64})
        row = report["modules"][0]["upstreams"][0]
        self.assertEqual(row["status"], "our_contribution_returned_upstream")
        self.assertFalse(row.get("review_required", False))
        self.assertEqual(row["reviewed_reconciliation"]["evidence_url"],
                         "https://example.org/full-diff")

    def test_three_version_lines_are_separate(self):
        p = {"id": "crosswire", "enabled": True, "base_url": "https://example.test/"}
        m = {"id": "some-kjv", "sword_id": "KJV", "version": "4.0.0",
             "upstreams": [{"provider": "crosswire", "module_id": "KJV", "last_integrated_version": "2.0"}]}
        local = {"kjv": {"version": "3.0.0", "install_source": "Bible Resources", "path": "/home/test"}}
        report = check([p], [m], local,
                       fetch_catalog=lambda _: {"kjv": {"version": "2.1", "conf_sha256": "a"}},
                       fetch_conf=lambda *_: {"version": "2.2", "conf_sha256": "b"})
        row = report["modules"][0]
        self.assertEqual(row["curated_version"], "4.0.0")
        self.assertEqual(row["installed_version"], "3.0.0")
        self.assertEqual(row["upstreams"][0]["upstream_version"], "2.2")
        self.assertEqual(row["upstreams"][0]["status"], "upstream_update_available")
        self.assertEqual(row["upstreams"][0]["checked_via"], "direct_conf")

    def test_direct_conf_fallback_to_archive(self):
        p = {"id": "ebible", "enabled": True, "base_url": "https://example.test/"}
        m = {"id": "kjv", "sword_id": "KJV", "version": "1.0.0",
             "upstreams": [{"provider": "ebible", "module_id": "KJV", "last_integrated_version": "1.0"}]}
        report = check([p], [m], {},
                       fetch_catalog=lambda _: {"kjv": {"version": "1.0", "conf_sha256": "a"}},
                       fetch_conf=lambda *_: (_ for _ in ()).throw(OSError("HTTP 404")))
        row = report["modules"][0]["upstreams"][0]
        self.assertEqual(row["status"], "up_to_date")
        self.assertEqual(row["checked_via"], "sword_catalog")
        self.assertIn("404", row["direct_check_warning"])

    def test_disabled_provider_cannot_return_update(self):
        m = {"id": "m", "sword_id": "KJV", "version": "1.0.0",
             "upstreams": [{"provider": "openbible", "module_id": "KJV", "last_integrated_version": "1.0"}]}
        report = check([{"id": "openbible", "enabled": False}], [m], {})
        self.assertEqual(report["modules"][0]["upstreams"][0]["status"], "provider_disabled_or_unknown")


if __name__ == "__main__":
    unittest.main()
