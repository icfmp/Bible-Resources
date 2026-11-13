"""Fail-closed synthetic tests for byte-preserving private zCom module wrapping."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_stock_candidate import private_relabel_config, _reader_identity_only_equivalence
from pilot_preflight import PilotError


class PrivateCommentaryCandidateTests(unittest.TestCase):
    def test_only_module_section_and_data_path_differ_from_exact_original_conf(self):
        original=(
            b"[MHCC]\n"
            b"Description=Original scholarly commentary\n"
            b"DataPath=./modules/comments/zcom/mhcc/\n"
            b"ModDrv=zCom\n"
            b"BlockType=BOOK\n"
            b"CompressType=ZIP\n"
            b"GlobalOptionFilter=OSISFootnotes\n"
            b"GlobalOptionFilter=OSISXRefs\n"
            b"Versification=KJV\n"
            b"DistributionLicense=Public Domain\n"
        )
        changed=private_relabel_config(original,"MHCC","BRMHCCReview")
        self.assertEqual(changed,original.replace(
            b"[MHCC]",b"[BRMHCCReview]",1
        ).replace(
            b"DataPath=./modules/comments/zcom/mhcc/",
            b"DataPath=./modules/comments/zcom/brmhccreview/",1
        ))
        self.assertEqual(changed.count(b"GlobalOptionFilter="),2)
        self.assertEqual(original.count(b"GlobalOptionFilter="),2)
        self.assertTrue(changed.endswith(b"DistributionLicense=Public Domain\n"))
        self.assertEqual(changed.count(b"Original scholarly commentary"),1)

    def test_actual_upstream_conf_header_comments_are_preserved(self):
        original=(
            b"# Original upstream source notice\n"
            b"; Maintainer comment\n\n"
            b"[MHCC]\n"
            b"DataPath=./modules/comments/zcom/mhcc/\n"
            b"ModDrv=zCom\nVersification=KJV\n"
        )
        result=private_relabel_config(original,"MHCC","BRMHCCReview")
        self.assertTrue(result.startswith(
            b"# Original upstream source notice\n; Maintainer comment\n\n[BRMHCCReview]\n"))
        self.assertIn(
            b"DataPath=./modules/comments/zcom/brmhccreview/\n",result)
        self.assertIn(b"ModDrv=zCom\nVersification=KJV\n",result)
        self.assertNotIn(b"[MHCC]",result)

    def test_crlf_source_conf_preserved_for_unmodified_metadata_lines(self):
        original=(
            b"[MHCC]\r\nDataPath=./modules/comments/zcom/mhcc/\r\n"
            b"ModDrv=zCom\r\nVersification=KJV\r\n"
        )
        changed=private_relabel_config(original,"MHCC","BRMHCCReview")
        self.assertEqual(changed.count(b"\r\n"),4)
        self.assertIn(b"ModDrv=zCom\r\n",changed)

    def test_different_original_datapath_refused(self):
        source=b"[MHCC]\nDataPath=./modules/texts/ztext/mhcc/\n"
        with self.assertRaises(PilotError):
            private_relabel_config(source,"MHCC","BRMHCCReview")

    def test_original_configuration_with_duplicate_path_blocked(self):
        source=(b"[MHCC]\n"
                b"DataPath=./modules/comments/zcom/mhcc/\n"
                b"DataPath=./modules/comments/zcom/mhcc/\n")
        with self.assertRaises(PilotError):
            private_relabel_config(source,"MHCC","BRMHCCReview")

    def test_original_config_cannot_be_encrypted(self):
        source=(b"[MHCC]\n"
                b"DataPath=./modules/comments/zcom/mhcc/\nCipherKey=secret\n")
        with self.assertRaises(PilotError):
            private_relabel_config(source,"MHCC","BRMHCCReview")

    def test_real_reader_module_identity_may_differ_without_body_rewrite(self):
        original=b"Genesis 1:1: Commentary body verbatim. (MHCC)"
        candidate=b"Genesis 1:1: Commentary body verbatim. (BRMHCCReview)"
        result=_reader_identity_only_equivalence(
            original,candidate,old_id="MHCC",candidate_id="BRMHCCReview"
        )
        self.assertEqual(result["original_module_label_replacements"],1)
        self.assertFalse(result["readback_byte_equal_before_identity_relabel"])
        self.assertTrue(result["same_plain_rendered_output_or_identity_only"])

    def test_reader_cannot_hide_even_one_changed_authorial_word(self):
        source=b"Matthew 1:1: Original commentary. (MHCC)"
        changed=b"Matthew 1:1: Altered commentary. (BRMHCCReview)"
        with self.assertRaises(PilotError):
            _reader_identity_only_equivalence(
                source,changed,old_id="MHCC",candidate_id="BRMHCCReview"
            )

    def test_reader_unchanged_literal_bytes_are_accepted(self):
        x=b"Unchanged module output"
        d=_reader_identity_only_equivalence(
            x,x,old_id="MHCC",candidate_id="BRMHCCReview"
        )
        self.assertEqual(d["original_module_label_replacements"],0)
        self.assertTrue(d["readback_byte_equal_before_identity_relabel"])

    def test_no_same_id_invalid_id_or_unverified_header(self):
        valid=(b"[MHCC]\n"
               b"DataPath=./modules/comments/zcom/mhcc/\n")
        for old,new in (("MHCC","MHCC"),("MHCC","../bad"),
                        ("Wrong","BRMHCCReview")):
            with self.subTest(old=old,new=new):
                with self.assertRaises(PilotError):
                    private_relabel_config(valid,old,new)


if __name__=="__main__":
    unittest.main()
