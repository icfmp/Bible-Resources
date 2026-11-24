"""Synthetic regression tests for all SWORD GlobalOptionFilter lines."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sword_option_filters import option_filter_errors


class TestSwordOptionFilters(unittest.TestCase):
    def scan(self, contents, kind="OSIS"):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.conf"
            path.write_text("[Synthetic]\nModDrv=zText\n" + contents,
                            encoding="utf-8")
            return option_filter_errors(path, kind)

    def test_registered_reference_filter(self):
        self.assertEqual(self.scan("GlobalOptionFilter=OSISFootnotes\n"
                                   "GlobalOptionFilter=OSISScripref\n"
                                   "GlobalOptionFilter=OSISHeadings\n"), [])

    def test_second_option_detects_historical_crossref_bug(self):
        errors = self.scan("GlobalOptionFilter=OSISFootnotes\n"
                           "GlobalOptionFilter=OSISXRefs\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("SWORD_OPTION_FILTER_UNREGISTERED", errors[0])
        self.assertIn("OSISXRefs", errors[0])

    def test_third_option_cannot_be_hidden_by_parse_conf(self):
        errors = self.scan("GlobalOptionFilter=OSISHeadings\n"
                           "GlobalOptionFilter=OSISFootnotes\n"
                           "GlobalOptionFilter=OSISXRefs\n")
        self.assertEqual(len(errors), 1)

    def test_duplicates(self):
        errors = self.scan("GlobalOptionFilter=OSISFootnotes\n"
                           "GlobalOptionFilter=OSISFootnotes\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("DUPLICATE", errors[0])

    def test_bad_format_and_typo(self):
        self.assertTrue(any("UNREGISTERED" in e for e in
                            self.scan("GlobalOptionFilter=ThMLScripref\n")))
        self.assertTrue(any("UNREGISTERED" in e for e in
                            self.scan("GlobalOptionFilter=OSISScriprefs\n")))
        self.assertTrue(any("MALFORMED" in e for e in
                            self.scan("GlobalOptionFilter=\n")))

    def test_no_filters_or_comment_only(self):
        self.assertEqual(self.scan(""), [])
        self.assertEqual(self.scan(";GlobalOptionFilter=OSISXRefs\n"), [])

    def test_registered_other_formats(self):
        self.assertEqual(self.scan("GlobalOptionFilter=ThMLScripref\n",
                                   "ThML"), [])
        self.assertEqual(self.scan("GlobalOptionFilter=GBFFootnotes\n",
                                   "GBF"), [])

    def test_parameterized_reference_links(self):
        good = ("GlobalOptionFilter=OSISReferenceLinks|Reference Material Links|"
                "Show links.|x-glossary||On\n")
        self.assertEqual(self.scan(good), [])
        self.assertTrue(self.scan("GlobalOptionFilter=OSISReferenceLinks\n"))

    def test_real_lsg_conf_is_registered(self):
        conf = ROOT / "modules/lsg-1910/payload/mods.d/brlsg1910.conf"
        self.assertEqual(option_filter_errors(conf, "OSIS"), [])


if __name__ == "__main__":
    unittest.main()
