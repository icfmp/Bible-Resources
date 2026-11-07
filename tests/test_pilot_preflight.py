"""Synthetic, fully offline ZIP preflight tests; no real Bible text needed."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pilot_preflight import PilotError, inspect_archive, inspect_pilot, main


def create_sword(path, *, module="fraLSG1910eb", driver="zText",
                 conf_name=None, extra=None):
    conf_name = conf_name or f"mods.d/{module.lower()}.conf"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(conf_name, f"[{module}]\nVersion=1.0\nModDrv={driver}\n"
                  "SourceType=OSIS\nVersification=KJV\nLang=fr\nEncoding=UTF-8\n")
        z.writestr("modules/texts/ztext/ls/file.bdt", b"test payload")
        for name, value in extra or []:
            z.writestr(name, value)


class PilotPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = json.loads((ROOT / "config/pilot-sources.json").read_text())

    def test_lsg_without_text_mutation_and_with_metadata(self):
        path = self.root / "lsg.zip"
        create_sword(path)
        before = path.read_bytes()
        report = inspect_archive(path, source_kind="sword",
                                 expected_module_id="fraLSG1910eb",
                                 expected_category="bible")
        self.assertEqual(report["sword_conf"]["module_id"], "fraLSG1910eb")
        self.assertEqual(report["sword_conf"]["category"], "bible")
        self.assertEqual(report["sword_conf"]["driver"], "zText")
        self.assertEqual(report["member_count"], 2)
        self.assertEqual(path.read_bytes(), before)

    def test_full_mhc_zcom4_accepted_and_distinct_from_mhcc(self):
        path = self.root / "mhc.zip"
        create_sword(path, module="MHC", driver="zCom4")
        report = inspect_pilot("mhc", path, config=self.config)
        self.assertEqual(report["sword"]["sword_conf"]["driver"], "zCom4")
        self.assertFalse(report["approved_for_publication"])
        with self.assertRaisesRegex(PilotError, "module ID mismatch"):
            inspect_archive(path, source_kind="sword", expected_module_id="MHCC",
                            expected_category="commentary")

    def test_source_zip_optional_only_for_mhc_and_required_for_lsg(self):
        path = self.root / "lsg.zip"
        create_sword(path)
        with self.assertRaisesRegex(PilotError, "Source archive must"):
            inspect_pilot("lsg", path, config=self.config)
        source = self.root / "usfm.zip"
        with zipfile.ZipFile(source, "w") as z:
            z.writestr("fraLSG/GEN.usfm", b"\\id GEN\n")
        report = inspect_pilot("lsg", path, source, config=self.config)
        self.assertEqual(report["authored"]["format_claim"], "USFM")
        self.assertFalse(report["source_to_sword_text_verified"])

    def test_cannot_silently_accept_mhc_with_wrong_category(self):
        path = self.root / "mhc.zip"
        create_sword(path, module="MHC", driver="zText")
        with self.assertRaisesRegex(PilotError, "category or driver"):
            inspect_pilot("mhc", path, config=self.config)

    def test_rejects_traversal_absolute_and_windows_paths(self):
        for i, unsafe in enumerate(("../outside.txt", "/tmp/path",
                                    "modules/../../oops", "modules\\evil")):
            with self.subTest(unsafe=unsafe):
                path = self.root / f"unsafe{i}.zip"
                create_sword(path, extra=[(unsafe, b"x")])
                with self.assertRaisesRegex(PilotError, "unsafe ZIP"):
                    inspect_archive(path, source_kind="sword",
                                    expected_module_id="fraLSG1910eb",
                                    expected_category="bible")

    def test_rejects_duplicate_casefolded_path(self):
        path = self.root / "duplicate.zip"
        create_sword(path, extra=[("MODS.D/FRALSG1910EB.CONF", b"[Other]\n")])
        with self.assertRaisesRegex(PilotError, "duplicate ZIP"):
            inspect_archive(path, source_kind="sword",
                            expected_module_id="fraLSG1910eb",
                            expected_category="bible")

    def test_rejects_symlink_file(self):
        path = self.root / "link.zip"
        with zipfile.ZipFile(path, "w") as z:
            conf = zipfile.ZipInfo("mods.d/fraLSG1910eb.conf")
            z.writestr(conf, b"[fraLSG1910eb]\nModDrv=zText\n")
            link = zipfile.ZipInfo("modules/malicious")
            link.create_system = 3
            link.external_attr = (0o120777 << 16)
            z.writestr(link, "../outside")
        with self.assertRaisesRegex(PilotError, "unsafe ZIP"):
            inspect_archive(path, source_kind="sword",
                            expected_module_id="fraLSG1910eb",
                            expected_category="bible")

    def test_rejects_broken_zip_and_missing_conf_or_payload(self):
        broken = self.root / "broken.zip"
        broken.write_text("not a zip")
        with self.assertRaises(zipfile.BadZipFile):
            inspect_archive(broken, source_kind="sword",
                            expected_module_id="fraLSG1910eb", expected_category="bible")
        missing = self.root / "missing.zip"
        with zipfile.ZipFile(missing, "w") as z:
            z.writestr("notes.txt", b"hello")
        with self.assertRaisesRegex(PilotError, r"exactly one mods.d"):
            inspect_archive(missing, source_kind="sword",
                            expected_module_id="fraLSG1910eb", expected_category="bible")

    def test_blocked_report_replaces_old_success(self):
        file = self.root / "bad.zip"
        file.write_text("no ZIP")
        report = self.root / "report.json"
        report.write_text('{"status":"inspected_not_approved"}')
        status = main(["--pilot", "lsg", "--sword-zip", str(file),
                       "--report", str(report)])
        self.assertEqual(status, 1)
        content = json.loads(report.read_text())
        self.assertEqual(content["status"], "blocked")
        self.assertFalse(content["approved_for_publication"])


if __name__ == "__main__":
    unittest.main()
