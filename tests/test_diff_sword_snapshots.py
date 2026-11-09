"""Offline update drift tests with only synthetic, non-Scripture SWORD payloads."""
import io
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diff_sword_snapshots import compare_snapshots, SnapshotError


class SnapshotDriftTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.home = Path(t.name)
        self.old = self.home / "old"
        self.new = self.home / "new"
        self._write(self.old, version="1.0")
        self._write(self.new, version="1.0")

    def _write(self, directory, *, version, data=b"SYNTHETIC-A",
               system="KJV", driver="RawText"):
        (directory / "mods.d").mkdir(parents=True, exist_ok=True)
        path = directory / "modules/texts/rawtext/fixture"
        path.mkdir(parents=True, exist_ok=True)
        (directory / "mods.d/fixture.conf").write_text(
            "[Fixture]\nVersion=" + version + "\n"
            "ModDrv=" + driver + "\n"
            "Versification=" + system + "\n"
            "DataPath=./modules/texts/rawtext/fixture/\n",
            encoding="utf-8")
        (path / "ot").write_bytes(data)

    def _zip(self, source: Path, target: Path, compress=zipfile.ZIP_DEFLATED):
        with zipfile.ZipFile(target, "w", compression=compress) as archive:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, arcname=path.relative_to(source).as_posix())
        return target

    def test_identical_module_files_are_not_source_parity_proof(self):
        report = compare_snapshots(self.old, self.new, "Fixture")
        self.assertEqual(report["status"], "file_bytes_identical_not_source_equivalence")
        self.assertFalse(report["actual_binary_files_changed"])
        self.assertFalse(report["source_edition_identity_verified"])
        self.assertFalse(report["editorial_approval"])
        self.assertFalse(report["published"])
        self.assertNotIn("SYNTHETIC-A", json.dumps(report))

    def test_same_version_actual_binary_change_is_detected(self):
        (self.new / "modules/texts/rawtext/fixture/ot").write_bytes(b"SYNTHETIC-B")
        result = compare_snapshots(self.old, self.new, "Fixture")
        self.assertEqual(result["status"], "same_version_binary_payload_changed_requires_review")
        self.assertTrue(result["actual_binary_files_changed"])
        self.assertEqual(result["changed_file_count"], 1)
        self.assertEqual(result["first_changed_paths"],
                         ["modules/texts/rawtext/fixture/ot"])
        self.assertEqual(result["previous_version"], "1.0")
        self.assertEqual(result["candidate_version"], "1.0")

    def test_same_version_only_conf_changed(self):
        p = self.new / "mods.d/fixture.conf"
        p.write_text(p.read_text() + "History_1.0=Edited metadata\n")
        result = compare_snapshots(self.old, self.new, "Fixture")
        self.assertEqual(result["status"], "same_version_metadata_changed_requires_review")
        self.assertFalse(result["actual_binary_files_changed"])
        self.assertTrue(result["config_changed"])

    def test_higher_upstream_version_always_requires_review(self):
        self._write(self.new, version="1.1", data=b"SYNTHETIC-B")
        self.assertEqual(compare_snapshots(self.old, self.new, "Fixture")["status"],
                         "newer_upstream_snapshot_requires_review")

    def test_older_snapshot_always_requires_review(self):
        self._write(self.old, version="1.2")
        self.assertEqual(compare_snapshots(self.old, self.new, "Fixture")["status"],
                         "older_upstream_snapshot_requires_review")

    def test_date_and_module_numeric_version_are_not_comparable(self):
        self._write(self.old, version="2026-10-29")
        self._write(self.new, version="100.0", data=b"SYNTHETIC-B")
        self.assertEqual(compare_snapshots(self.old, self.new, "Fixture")["status"],
                         "unorderable_version_or_baseline_requires_review")

    def test_changed_v11n_or_driver_blocks_simple_equivalence(self):
        self._write(self.new, version="1.1", system="NRSV")
        self.assertEqual(compare_snapshots(self.old, self.new, "Fixture")["status"],
                         "native_driver_or_versification_changed_requires_review")
        self._write(self.new, version="1.1", system="KJV", driver="zText")
        self.assertEqual(compare_snapshots(self.old, self.new, "Fixture")["status"],
                         "native_driver_or_versification_changed_requires_review")

    def test_different_module_identity_refused_even_if_same_title(self):
        p = self.new / "mods.d/fixture.conf"
        p.write_text(p.read_text().replace("[Fixture]", "[Other]"))
        with self.assertRaisesRegex(SnapshotError, "identity"):
            compare_snapshots(self.old, self.new, "Fixture")

    def test_added_and_removed_binary_paths_are_reported(self):
        path = self.new / "modules/texts/rawtext/fixture/nt"
        path.write_bytes(b"SYNTHETIC-NT")
        report = compare_snapshots(self.old, self.new, "Fixture")
        self.assertEqual(report["added_file_count"], 1)
        self.assertTrue(report["actual_binary_files_changed"])
        path.unlink()
        (self.old / "modules/texts/rawtext/fixture/ot").unlink()
        with self.assertRaisesRegex(SnapshotError, "binary module"):
            compare_snapshots(self.old, self.new, "Fixture")

    def test_uncompressed_and_compressed_zips_compare_inner_file_bytes(self):
        zipped_a = self._zip(self.old, self.home / "a.zip", zipfile.ZIP_STORED)
        zipped_b = self._zip(self.new, self.home / "b.zip", zipfile.ZIP_DEFLATED)
        report = compare_snapshots(zipped_a, zipped_b, "Fixture")
        self.assertEqual(report["status"], "file_bytes_identical_not_source_equivalence")
        self.assertEqual(report["previous_file_manifest_sha256"],
                         report["candidate_file_manifest_sha256"])

    def test_zip_and_directory_parity(self):
        packaged = self._zip(self.new, self.home / "new.zip")
        report = compare_snapshots(self.old, packaged, "Fixture")
        self.assertFalse(report["actual_binary_files_changed"])
        self.assertEqual(report["changed_file_count"], 0)

    def test_archive_path_traversal_is_blocked(self):
        bad = self.home / "bad.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr("../evil", "X")
            archive.writestr("mods.d/fixture.conf", (self.old / "mods.d/fixture.conf").read_bytes())
            archive.writestr("modules/texts/rawtext/fixture/ot", "X")
        with self.assertRaisesRegex(SnapshotError, "path"):
            compare_snapshots(self.old, bad, "Fixture")

    def test_zip_duplicate_members_and_case_collisions_blocked(self):
        bad = self.home / "duplicates.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr("mods.d/fixture.conf", (self.old / "mods.d/fixture.conf").read_bytes())
            archive.writestr("modules/texts/rawtext/fixture/ot", b"A")
            archive.writestr("modules/texts/rawtext/fixture/OT", b"B")
        with self.assertRaisesRegex(SnapshotError, "case-colliding"):
            compare_snapshots(self.old, bad, "Fixture")

    def test_zip_symlink_is_blocked(self):
        bad = self.home / "symlink.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr("mods.d/fixture.conf", (self.old / "mods.d/fixture.conf").read_bytes())
            entry = zipfile.ZipInfo("modules/texts/rawtext/fixture/ot")
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(entry, "sensitive_target")
        with self.assertRaisesRegex(SnapshotError, "symlink"):
            compare_snapshots(self.old, bad, "Fixture")

    def test_local_symlink_is_blocked(self):
        p = self.new / "modules/texts/rawtext/fixture/link"
        p.symlink_to(self.old / "mods.d/fixture.conf")
        with self.assertRaisesRegex(SnapshotError, "Symlink"):
            compare_snapshots(self.old, self.new, "Fixture")

    def test_missing_conf_or_module_binary_fails_closed(self):
        (self.new / "mods.d/fixture.conf").unlink()
        with self.assertRaisesRegex(SnapshotError, "configuration"):
            compare_snapshots(self.old, self.new, "Fixture")

    def test_unknown_module_identifier_fails_closed(self):
        with self.assertRaisesRegex(SnapshotError, "module ID"):
            compare_snapshots(self.old, self.new, "../Fixture")


if __name__ == "__main__":
    unittest.main()
