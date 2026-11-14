"""Invented-only mixed original I and K OSIS transport regression."""
import sys
from pathlib import Path
import unittest
from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_osis_mixed_transport_probe import (
    build_mixed_original_transport, build_complete_original_transport,
    validate_private_index_alias_preview, _native_same_chapter_ranges,
    classify_chapter_reader_repetition, probe_private_chapter_reader_repetition,
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


    def test_provisional_alias_inherits_single_authorial_section_without_gap_fill(self):
        first=b'<div type="section"><title>Original invented joint section</title></div>'
        separate=b'<div type="section"><title>Original invented middle section</title></div>'
        intros={"Gen":b"<div/>","Gen.1":b"<chapter/>"}
        numbered={"Gen.1":[
            ("Gen.1.1",first),("Gen.1.2",first),
            ("Gen.1.3",separate),("Gen.1.4",separate)
        ]}
        aliases={
            "Gen.1.5":{"link_to":"Gen.1.1","source_raw_sha256":__import__("hashlib").sha256(first).hexdigest()},
            "Gen.1.7":{"link_to":"Gen.1.1","source_raw_sha256":__import__("hashlib").sha256(first).hexdigest()},
            "Gen.1.8":{"link_to":"Gen.1.1","source_raw_sha256":__import__("hashlib").sha256(first).hexdigest()},
        }
        xml,info=build_complete_original_transport(
            intros,numbered,work_id="PreviewTest",
            provisional_index_aliases=aliases
        )
        root=etree.fromstring(xml)
        entries=root.xpath(
            "//*[local-name()='div' and @annotateType='commentary']"
        )
        self.assertEqual(len(entries),2)
        self.assertEqual(entries[0].attrib["annotateRef"],
                         "Gen.1.1-Gen.1.2 Gen.1.5 Gen.1.7-Gen.1.8")
        self.assertEqual(entries[1].attrib["annotateRef"],"Gen.1.3-Gen.1.4")
        self.assertEqual(info["provisional_index_alias_count"],3)
        self.assertTrue(info["provisional_index_aliases_not_editorially_approved"])
        self.assertEqual(xml.count(first),1)
        self.assertEqual(xml.count(separate),1)

    def test_index_link_preview_blocks_wrong_hash_cross_chapter_and_overwrite(self):
        from hashlib import sha256
        original=b"<div><title>Unchanged synthetic original</title></div>"
        occupied={"Gen.1":[("Gen.1.1",original)]}
        good={"link_to":"Gen.1.1","source_raw_sha256":sha256(original).hexdigest()}
        for aliases in (
            {"Gen.1.1":good},
            {"Gen.2.2":good},
            {"Exod.1.2":good},
            {"Gen.1.2":{"link_to":"Gen.1.99","source_raw_sha256":good["source_raw_sha256"]}},
            {"Gen.1.2":{**good,"source_raw_sha256":"0"*64}},
            {"Gen.1.2":{**good,"link_to":"Exod.1.1"}},
            {"Gen.1.0":good},
        ):
            with self.subTest(aliases=aliases):
                with self.assertRaises(ValueError):
                    validate_private_index_alias_preview(occupied,aliases)
        self.assertEqual(_native_same_chapter_ranges([
            "Gen.1.1","Gen.1.2","Gen.1.5","Gen.1.7"
        ]),"Gen.1.1-Gen.1.2 Gen.1.5 Gen.1.7")
        with self.assertRaises(ValueError):
            _native_same_chapter_ranges(["Gen.1.1","Gen.2.2"])



class ReaderRepetitionTests(unittest.TestCase):
    def test_complete_chapter_one_copy_vs_two_copies(self):
        master=(" ".join(f"inventedword{n}" for n in range(1,125))).encode()
        chapter_single=b"Chapter beginning " + master + b" Chapter ending."
        chapter_double=b"Chapter beginning " + master + b" " + master + b" Chapter ending."
        single=classify_chapter_reader_repetition(master, chapter_single)
        twice=classify_chapter_reader_repetition(master,chapter_double)
        self.assertEqual(single["classification"],"EXACT_COMMENTARY_EXCERPT_APPEARS_ONCE")
        self.assertEqual(single["reliable_count"],1)
        self.assertEqual(twice["classification"],"REPEATED_EXACT_COMMENTARY_EXCERPT")
        self.assertEqual(twice["reliable_count"],2)

    def test_partial_chapter_or_too_short_master_is_inconclusive(self):
        master=(" ".join(f"word{n}" for n in range(1,125))).encode()
        missing=b"Unrelated independent commentary omitted from this screen."
        self.assertIsNone(
            classify_chapter_reader_repetition(master,missing)["reliable_count"]
        )
        short=b"one two three four"
        self.assertEqual(
            classify_chapter_reader_repetition(short,master)["classification"],
            "INSUFFICIENT_UNIQUE_ORIGINAL_PROSE"
        )
        with self.assertRaises(ValueError):
            classify_chapter_reader_repetition(master,master,width=7)

    def test_real_reader_difference_is_reported_not_approved(self):
        from unittest.mock import patch
        from tempfile import TemporaryDirectory
        master=(" ".join(f"synthetic{n}" for n in range(1,125))).encode()
        cases={
            ("MHCC","Gen 1:1"):master,
            ("BRIndexProbe","Gen 1:1"):master,
            ("MHCC","Gen 1"):b"Beginning " +master + b" End",
            ("BRIndexProbe","Gen 1"):b"Beginning " +master + b" " +master+b" End",
        }
        def mocked_query(module,reference,**kwargs):
            return 0,cases[(module,reference)]
        with TemporaryDirectory() as tmp, patch(
            "pilot_subprocess.query",side_effect=mocked_query
        ):
            p=Path(tmp)
            original=p/"original";original.mkdir()
            rebuilt=p/"candidate";rebuilt.mkdir()
            observed=probe_private_chapter_reader_repetition(
                original,rebuilt,"MHCC","BRIndexProbe",{
                    "Gen.1.2":{"link_to":"Gen.1.1","source_raw_sha256":"a"*64},
                    "Gen.1.3":{"link_to":"Gen.1.1","source_raw_sha256":"a"*64},
                }
            )
        self.assertEqual(observed["chapters_with_proven_increased_repeat_count"],1)
        self.assertFalse(observed["publication_authorized"])
        self.assertFalse(observed["chapter_deduplication_in_Xiphos_or_Bible_verified"])
        self.assertEqual(
            observed["cases"][0]["status"],"NEW_ALIAS_CHAPTER_REPETITION_INCREASE"
        )


if __name__=="__main__":
    unittest.main()
