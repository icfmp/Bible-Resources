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
