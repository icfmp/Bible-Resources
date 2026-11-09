"""Hash-pinned and source-preserving first release packaging tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
import hashlib
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from promote_sword_preview import promote


class SwordPromotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.src = self.home / "source.zip"
        self.out = self.home / "release.zip"
        self.conf = self.home / "module.conf"
        self.data = {
            "nt": b"NT data", "nt.vss": b"NT index",
            "ot": b"OT data", "ot.vss": b"OT index",
        }
        with ZipFile(self.src, "w", compression=ZIP_DEFLATED) as zip_file:
            zip_file.writestr("mods.d/verifiedpreview.conf",
                              "[VerifiedPreview]\nDataPath=./modules/texts/rawtext/verifiedpreview/\n")
            for name, value in self.data.items():
                zip_file.writestr("modules/texts/rawtext/verifiedpreview/" + name, value)
        self.sha = hashlib.sha256(self.src.read_bytes()).hexdigest()
        self.conf.write_text(
            "[PublishedModule]\n"
            "DataPath=./modules/texts/rawtext/publishedmodule/\n"
            "ModDrv=RawText\n"
            "Encoding=UTF-8\n"
            "Versification=Segond\n"
            "DistributionLicense=Public Domain\n",
            encoding="utf-8",
        )

    def promote(self, **kwargs):
        options = dict(
            expected_source_sha256=self.sha,
            source_id="VerifiedPreview",
            destination_id="PublishedModule",
            config=self.conf,
        )
        options.update(kwargs)
        return promote(self.src, self.out, **options)

    def test_exact_data_bytes_and_deterministic_archive(self):
        before = self.src.read_bytes()
        result = self.promote()
        self.assertTrue(result["data_byte_equal"])
        self.assertEqual(result["status"], "exact_sword_payload_promoted_with_reviewed_metadata")
        with ZipFile(self.out) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()), 5)
            for name, value in self.data.items():
                self.assertEqual(archive.read("modules/texts/rawtext/publishedmodule/" + name), value)
            self.assertEqual(archive.read("mods.d/publishedmodule.conf"), self.conf.read_bytes())
        self.assertEqual(before, self.src.read_bytes())
        self.assertEqual(hashlib.sha256(self.out.read_bytes()).hexdigest(),
                         result["release_zip_sha256"])
        self.out.unlink()
        self.assertEqual(result["release_zip_sha256"], self.promote()["release_zip_sha256"])

    def test_reject_changed_input_digest_without_writing(self):
        with self.assertRaises(ValueError):
            self.promote(expected_source_sha256="0" * 64)
        self.assertFalse(self.out.exists())

    def test_reject_metadata_incorrect_index_or_storage(self):
        self.conf.write_text(self.conf.read_text().replace(
            "Versification=Segond", "Versification=NRSV"), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.promote()
        self.assertFalse(self.out.exists())

    def test_reject_unexpected_member_and_existing_destination(self):
        with ZipFile(self.src, "a") as archive:
            archive.writestr("unexpected", b"data")
        self.sha = hashlib.sha256(self.src.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.promote()
        self.assertFalse(self.out.exists())
        self.out.write_bytes(b"existing")
        with self.assertRaises(ValueError):
            self.promote()
        self.assertEqual(self.out.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
