"""Strict ZIP safety and exact binary identity for first LSG catalogue import."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZipInfo

from scripts.materialize_attested_lsg_release import verified_members


class AttestedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "source.zip"
        self.values = {
            "mods.d/test.conf": b"[Test]\n",
            "modules/texts/rawtext/test/ot": b"exact OT bytes",
            "modules/texts/rawtext/test/nt": b"exact NT bytes",
        }
        with ZipFile(self.path, "w") as z:
            for k, v in self.values.items():
                z.writestr(k, v)
        self.manifest = {
            "release_zip_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "files": {k: hashlib.sha256(v).hexdigest()
                      for k, v in self.values.items()},
        }

    def test_exact_bytes_are_recovered_without_rewriting(self):
        assert verified_members(self.path, self.manifest) == self.values

    def test_reject_changed_zip_even_when_zip_remains_crc_valid(self):
        with ZipFile(self.path, "a") as z:
            z.writestr("other", b"wrong")
        with self.assertRaisesRegex(ValueError, "Release ZIP"):
            verified_members(self.path, self.manifest)

    def test_reject_unexpected_entry_with_updated_container_checksum(self):
        with ZipFile(self.path, "a") as z:
            z.writestr("modules/texts/rawtext/test/extra", b"wrong")
        self.manifest["release_zip_sha256"] = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Unexpected SWORD"):
            verified_members(self.path, self.manifest)

    def test_reject_changed_payload_with_updated_zip_hash(self):
        self.manifest["files"]["modules/texts/rawtext/test/ot"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SWORD payload byte mismatch"):
            verified_members(self.path, self.manifest)

    def test_reject_symlinked_release_zip(self):
        other = self.path.parent / "link.zip"
        other.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, "Unsafe release archive"):
            verified_members(other, self.manifest)


if __name__ == "__main__":
    unittest.main()
