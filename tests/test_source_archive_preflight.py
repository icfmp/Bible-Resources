"""Synthetic, fully offline ZIP preflight tests; no real Bible text needed."""
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pilot_preflight import PilotError, inspect_archive


def create_sword(path, *, module="SyntheticBible", driver="zText",
                 conf_name=None, extra=None):
    conf_name = conf_name or f"mods.d/{module.lower()}.conf"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(conf_name, f"[{module}]\nVersion=1.0\nModDrv={driver}\n"
                  "SourceType=OSIS\nVersification=KJV\nLang=fr\nEncoding=UTF-8\n")
        z.writestr("modules/texts/ztext/ls/file.bdt", b"test payload")
        for name, value in extra or []:
            z.writestr(name, value)


class SourceArchivePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_synthetic_bible_without_text_mutation_and_with_metadata(self):
        path = self.root / "synthetic-bible.zip"
        create_sword(path)
        before = path.read_bytes()
        report = inspect_archive(path, source_kind="sword",
                                 expected_module_id="SyntheticBible",
                                 expected_category="bible")
        self.assertEqual(report["sword_conf"]["module_id"], "SyntheticBible")
        self.assertEqual(report["sword_conf"]["category"], "bible")
        self.assertEqual(report["sword_conf"]["driver"], "zText")
        self.assertEqual(report["member_count"], 2)
        self.assertEqual(path.read_bytes(), before)

    def test_zcom4_commentary_is_accepted_but_not_misidentified_as_another_module(self):
        path = self.root / "commentary.zip"
        create_sword(path, module="SyntheticCom", driver="zCom4")
        report = inspect_archive(
            path, source_kind="sword", expected_module_id="SyntheticCom",
            expected_category="commentary")
        self.assertEqual(report["sword_conf"]["driver"], "zCom4")
        with self.assertRaisesRegex(PilotError, "module ID mismatch"):
            inspect_archive(path, source_kind="sword", expected_module_id="OtherCom",
                            expected_category="commentary")

    def test_generic_authored_zip_inspection_does_not_assume_source_format(self):
        path = self.root / "original.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("original/GEN.usfm", b"\\\\id GEN\\n")
        before = path.read_bytes()
        report = inspect_archive(path, source_kind="authored")
        self.assertEqual(report["source_kind"], "authored")
        self.assertEqual(report["member_count"], 1)
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn("sword_conf", report)

    def test_commentary_driver_is_rejected_for_wrong_module_category(self):
        path = self.root / "commentary.zip"
        create_sword(path, module="SyntheticCom", driver="zText")
        with self.assertRaisesRegex(PilotError, "category or driver"):
            inspect_archive(path, source_kind="sword", expected_module_id="SyntheticCom",
                            expected_category="commentary")

    def test_rejects_traversal_absolute_and_windows_paths(self):
        for i, unsafe in enumerate(("../outside.txt", "/tmp/path",
                                    "modules/../../oops", "modules\\evil")):
            with self.subTest(unsafe=unsafe):
                path = self.root / f"unsafe{i}.zip"
                create_sword(path, extra=[(unsafe, b"x")])
                with self.assertRaisesRegex(PilotError, "unsafe ZIP"):
                    inspect_archive(path, source_kind="sword",
                                    expected_module_id="SyntheticBible",
                                    expected_category="bible")

    def test_rejects_duplicate_casefolded_path(self):
        path = self.root / "duplicate.zip"
        create_sword(path, extra=[("MODS.D/SYNTHETICBIBLE.CONF", b"[Other]\n")])
        with self.assertRaisesRegex(PilotError, "duplicate ZIP"):
            inspect_archive(path, source_kind="sword",
                            expected_module_id="SyntheticBible",
                            expected_category="bible")

    def test_rejects_symlink_file(self):
        path = self.root / "link.zip"
        with zipfile.ZipFile(path, "w") as z:
            conf = zipfile.ZipInfo("mods.d/SyntheticBible.conf")
            z.writestr(conf, b"[SyntheticBible]\nModDrv=zText\n")
            link = zipfile.ZipInfo("modules/malicious")
            link.create_system = 3
            link.external_attr = (0o120777 << 16)
            z.writestr(link, "../outside")
        with self.assertRaisesRegex(PilotError, "unsafe ZIP"):
            inspect_archive(path, source_kind="sword",
                            expected_module_id="SyntheticBible",
                            expected_category="bible")

    def test_rejects_broken_zip_and_missing_conf_or_payload(self):
        broken = self.root / "broken.zip"
        broken.write_text("not a zip")
        with self.assertRaises(zipfile.BadZipFile):
            inspect_archive(broken, source_kind="sword",
                            expected_module_id="SyntheticBible", expected_category="bible")
        missing = self.root / "missing.zip"
        with zipfile.ZipFile(missing, "w") as z:
            z.writestr("notes.txt", b"hello")
        with self.assertRaisesRegex(PilotError, r"exactly one mods.d"):
            inspect_archive(missing, source_kind="sword",
                            expected_module_id="SyntheticBible", expected_category="bible")



if __name__ == "__main__":
    unittest.main()
