"""Private second real Bible probe: synthetic safety unit tests only.

The separate Actions workflow downloads the real WEB original source and SWORD
zText module, but the ordinary Validate workflow never depends on eBible.
"""
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from real_second_bible_probe import (
    _safe_single_module, _source_counts_by_order, _reader_counts_by_order,
    SecondBibleError,
)
from diff_sword_snapshots import SnapshotError


class RealSecondBibleProbeTests(unittest.TestCase):
    def test_source_usfx_counts_with_more_than_one_book(self):
        usfx = (b'<usfx><book id="GEN"><c id="1"/>'
                b'<v id="1"/>One <v id="2"/>Two'
                b'</book><book id="EXO"><c id="1"/>'
                b'<v id="1"/>Three</book></usfx>')
        source, groups = _source_counts_by_order(usfx)
        self.assertEqual(source["original_books"], ["GEN", "EXO"])
        self.assertEqual([g["authored_verse_count"] for g in groups], [2, 1])

    def test_authorial_unnumbered_book_is_not_fabricated_as_missing_verse(self):
        usfx = (b'<usfx><book id="FRT"><p>Publisher introduction.</p></book>'
                b'<book id="GEN"><c id="1"/><v id="1"/>One</book></usfx>')
        metadata, groups = _source_counts_by_order(usfx)
        self.assertEqual(metadata["original_books"], ["FRT", "GEN"])
        self.assertEqual([g["authored_verse_count"] for g in groups], [0, 1])
        self.assertTrue(groups[0]["requires_unnumbered_intro_content_audit"])
        self.assertFalse(groups[1]["requires_unnumbered_intro_content_audit"])

    def test_reader_book_counts_preserve_real_native_inventory_order(self):
        keys = "Gen.1.1\nGen.1.2\nExod.1.1\nExod.1.2\nExod.2.1\n"
        groups = _reader_counts_by_order(keys)
        self.assertEqual([g["osis_book_id"] for g in groups], ["Gen", "Exod"])
        self.assertEqual([g["occupied_verse_count"] for g in groups], [2, 3])
        self.assertEqual(groups[1]["occupied_chapter_count"], 2)

    def test_unordered_return_to_previous_native_book_is_rejected(self):
        keys = "Gen.1.1\nExod.1.1\nGen.1.2\n"
        with self.assertRaisesRegex(SecondBibleError, "Noncontiguous"):
            _reader_counts_by_order(keys)

    def test_duplicate_reader_verse_rejected(self):
        with self.assertRaises(ValueError):
            _reader_counts_by_order("Gen.1.1\nGen.1.1\n")

    def test_safe_zip_to_private_sword_root_without_changing_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "module.zip"
            config = (b"[Example]\nVersion=1.0\nModDrv=zText\n"
                      b"Versification=KJV\n")
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("mods.d/example.conf", config)
                z.writestr("modules/texts/ztext/example/ot", b"PRIVATE-FIXTURE")
            before = archive.read_bytes()
            details = _safe_single_module(archive, root / "isolated-module")
            self.assertEqual(details["module_id"], "Example")
            self.assertEqual(details["original_version"], "1.0")
            self.assertEqual(details["original_driver"], "zText")
            self.assertEqual(details["original_versification"], "KJV")
            self.assertEqual(archive.read_bytes(), before)
            self.assertEqual((root / "isolated-module/payload/"
                              "modules/texts/ztext/example/ot").read_bytes(),
                             b"PRIVATE-FIXTURE")

    def test_non_bible_module_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "module.zip"
            config = b"[Example]\nVersion=1.0\nModDrv=zCom\n"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("mods.d/example.conf", config)
                z.writestr("modules/comments/zcom/example/ot", b"PRIVATE")
            with self.assertRaisesRegex(SecondBibleError, "supported Bible"):
                _safe_single_module(archive, root / "isolated")

    def test_unsafe_zip_path_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "malicious.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("mods.d/example.conf", b"[Example]\nVersion=1.0\nModDrv=zText\n")
                z.writestr("../leak", b"SECRET")
                z.writestr("modules/texts/ztext/example/ot", b"PRIVATE")
            with self.assertRaises(SnapshotError):
                _safe_single_module(archive, root / "isolated")
            self.assertFalse((root / "leak").exists())


if __name__ == "__main__":
    unittest.main()
