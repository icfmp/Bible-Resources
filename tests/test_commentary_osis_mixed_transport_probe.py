"""Invented-only mixed original I and K OSIS transport regression."""
import sys
from pathlib import Path
import unittest
from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_osis_mixed_transport_probe import (
    build_mixed_original_transport, build_complete_original_transport,
    mixed_transport_checks_pass, _COVERAGE_FIELDS
)


class MixedOriginalTransportTests(unittest.TestCase):
    def test_original_book_intro_chapter_intro_and_verses_all_inside_xml_unchanged(self):
        book=b'<div type="book"/>'
        intro=b'<chapter osisID="Gen.36"/><div type="section"/>'
        verse=b'<title>Invented chapter prose</title><div>Text for chapter.</div>'
        xml,meta=build_mixed_original_transport(
            "Gen.36",book,intro,
            [("Gen.36.1",verse),("Gen.36.2",verse)],
            work_id="MixedTest"
        )
        self.assertIn(book,xml)
        self.assertIn(intro,xml)
        self.assertIn(verse,xml)
        self.assertEqual(meta["numbered_source_keys"],2)
        self.assertEqual(meta["numbered_source_groups"],1)
        self.assertFalse(meta["source_intro_raw_modified"])
        self.assertFalse(meta["source_k_raw_modified"])
        self.assertFalse(meta["source_published"])
        document=etree.fromstring(xml)
        self.assertEqual(len(document.xpath(
            "//*[local-name()='div' and @annotateRef='Gen.36.1-Gen.36.2']"
        )),1)

    def test_chapter_range_mismatch_and_binary_material_are_blocked(self):
        for rows in (
            [("Gen.35.1",b"<p>Other chapter</p>")],
            [("Gen.36.2",b"<p>later</p>"),
             ("Gen.36.1",b"<p>earlier</p>")],
            [("Gen.36.1",b"<p>binary\x00</p>")]
        ):
            with self.assertRaises(ValueError):
                build_mixed_original_transport(
                    "Gen.36",b"<div/>",b"<chapter/>",rows,
                    work_id="MixedTest"
                )


    def test_real_readback_gate_checks_every_I_and_K_property(self):
        def coverage(n):
            return {field:n for field in _COVERAGE_FIELDS}
        base = dict(
            expected_intro_keys=2, expected_numbered_keys=13,
            intro_coverage=coverage(2), numbered_coverage=coverage(13),
            missing_intro_keys=[], missing_numbered_keys=[],
            extra_intro_keys=[], extra_numbered_keys=[]
        )
        self.assertTrue(mixed_transport_checks_pass(**base))
        for field in _COVERAGE_FIELDS:
            broken_intro = dict(coverage(2))
            broken_intro[field] = 1
            self.assertFalse(mixed_transport_checks_pass(
                **{**base, "intro_coverage":broken_intro}))
            broken_numbered = dict(coverage(13))
            broken_numbered[field] = 12
            self.assertFalse(mixed_transport_checks_pass(
                **{**base, "numbered_coverage":broken_numbered}))
        for field, value in (
            ("missing_intro_keys", ["2John"]),
            ("missing_numbered_keys", ["2John.1.3"]),
            ("extra_intro_keys", ["Jude"]),
            ("extra_numbered_keys", ["2John.1.14"]),
            ("expected_numbered_keys", 0),
            ("expected_intro_keys", 3)
        ):
            self.assertFalse(mixed_transport_checks_pass(
                **{**base, field:value}))
        self.assertFalse(mixed_transport_checks_pass(
            **{**base, "numbered_coverage":
               {**coverage(13), "source_keys_present":True}}))


    def test_complete_original_transport_groups_only_adjacent_identical_K(self):
        first=b'<div type="section"><title>Invented A</title>Text A.</div>'
        later=b'<div type="section"><title>Invented B</title>Text B.</div>'
        intro={
            "Gen":b"<div type='book'/>",
            "Gen.1":b"<chapter osisID='Gen.1'/>",
            "Gen.2":b"<chapter osisID='Gen.2'/><title>Invented intro only</title>",
            "Exod":b"<div type='book'/>",
            "Exod.1":b"<chapter osisID='Exod.1'/>",
        }
        numbered={
            "Gen.1":[("Gen.1.1",first),("Gen.1.2",first),
                     ("Gen.1.4",first),("Gen.1.5",later)],
            "Exod.1":[("Exod.1.1",later)]
        }
        xml, info=build_complete_original_transport(
            intro,numbered,work_id="FullTest"
        )
        self.assertEqual(info["source_book_intro_count"],2)
        self.assertEqual(info["source_chapter_intro_count"],3)
        self.assertEqual(info["source_numbered_key_count"],5)
        self.assertEqual(info["source_numbered_group_count"],4)
        self.assertTrue(info["original_I_K_raw_markup_not_rewritten"])
        root=etree.fromstring(xml)
        targets=root.xpath(
            "//*[local-name()='div' and @annotateType='commentary']/@annotateRef"
        )
        self.assertEqual(targets,[
            "Gen.1.1-Gen.1.2","Gen.1.4","Gen.1.5","Exod.1.1"
        ])
        self.assertEqual(len(root.xpath(
            "//*[local-name()='div' and @type='chapter' and @osisID='Gen.2']"
        )),1)
        self.assertNotIn(b'annotateRef="Gen.2.',xml)

    def test_complete_transport_refuses_orphan_and_untrusted_entries(self):
        good={"Gen":b"<div/>","Gen.1":b"<chapter/>"}
        for intros, numbered in (
            ({"Gen.1":b"<chapter/>","Exod":b"<div/>"},
             {"Gen.1":[("Gen.1.1",b"<div/>")]}),
            (good,{"Exod.1":[("Exod.1.1",b"<div/>")]}),
            (good,{"Gen.1":[("Gen.2.1",b"<div/>")]}),
            (good,{"Gen.1":[("Gen.1.2",b"<div/>"),
                            ("Gen.1.1",b"<div/>")]}),
            (good,{"Gen.1":[("Gen.1.1",b"<div>\x00</div>")]}),
        ):
            with self.subTest(intros=list(intros),numbered=list(numbered)):
                with self.assertRaises(ValueError):
                    build_complete_original_transport(
                        intros,numbered,work_id="FullTest"
                    )


if __name__=="__main__":
    unittest.main()
