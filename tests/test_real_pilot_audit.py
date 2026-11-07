"""Offline real-module audit wrapper contract, with synthetic SWORD/USFM archives."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_real_pilot import run, usfm_summary


class ActualSourceAuditWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.sword=self.root/"sword.zip"
        with zipfile.ZipFile(self.sword,"w") as z:
            z.writestr("mods.d/fralsg1910eb.conf",
                "[fraLSG1910eb]\nModDrv=zText\nLang=fr\nVersion=1.0\n"
                "SourceType=OSIS\nVersification=NRSV\n")
            z.writestr("modules/texts/ztext/ls/test.bdt",b"dummy SWORD data")
        self.authored=self.root/"authored.zip"
        with zipfile.ZipFile(self.authored,"w") as z:
            z.writestr("fraLSG/01-GEN.usfm",
                       "\\id GEN\n\\c 1\n\\p\n\\v 1 Original source example.\n\\q1 A line\n\\x + Ex 1\n")
        self.fake=self.root/"diatheke"
        self.fake.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "assert sys.argv[5]=='-k'\n"
            "print('<p>Sample scoped text</p>')\n"
        )
        self.fake.chmod(0o700)

    def test_report_contains_only_structural_signals(self):
        r=run("lsg",self.sword,authored_zip=self.authored,diatheke=str(self.fake))
        self.assertEqual(r["sword"]["module_id"],"fraLSG1910eb")
        self.assertEqual(r["authored_usfm"]["marker_totals"]["v"],1)
        self.assertEqual(r["authored_usfm"]["marker_totals"]["q1"],1)
        self.assertEqual(r["sword"]["samples"][0]["render_markup_signal_counts"]["paragraph"],1)
        self.assertNotIn("Sample scoped text",json.dumps(r))
        self.assertNotIn("Original source example",json.dumps(r))
        self.assertFalse(r["full_content_fidelity_verified"])
        self.assertFalse(r["published_content"])

    def test_source_zip_fingerprint_is_not_a_source_text_match(self):
        r=usfm_summary(self.authored)
        self.assertTrue(r["content_not_compared_to_sword"])
        self.assertEqual(r["files_with_usfm"],1)


if __name__=="__main__":
    unittest.main()
