"""Invented-only mixed original I and K OSIS transport regression."""
import sys
from hashlib import sha256
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
from lxml import etree

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_osis_mixed_transport_probe import (
    build_mixed_original_transport, build_complete_original_transport,
    validate_private_index_alias_preview, _native_same_chapter_ranges,
    classify_chapter_reader_repetition, probe_private_chapter_reader_repetition,
    probe_native_original_link_identity,
    mixed_transport_checks_pass, _COVERAGE_FIELDS,
    privately_stage_versioned_zcom_zip,
    private_rekey_sword_commentary_conf,
    verify_private_versioned_commentary_conf_delta
)


class PrivateCommentaryMetadataDeltaTests(unittest.TestCase):
    def test_exact_private_edition_delta_preserves_all_upstream_claims(self):
        source = (
            "[Curated]\nDescription=Invented test commentary\n"
            "DataPath=./modules/comments/zcom/curated/\n"
            "ModDrv=zCom\nSourceType=OSIS\nVersification=KJV\n"
            "BlockType=BOOK\nCompressType=ZIP\n"
            "Version=0.1.0\nInstallSize=120\n"
            "DistributionLicense=Public Domain\n"
            "TextSource=https://example.invalid/source\n"
            "About=Source printing assertion, not curator verified\n"
            "SwordVersionDate=2020-02-03\n"
            "GlobalOptionFilter=OSISHeadings\n"
        ).encode("utf-8")
        staged = (
            source.decode("utf-8")
            .replace("BlockType=BOOK", "BlockType=CHAPTER")
            .replace("Version=0.1.0", "Version=0.1.1")
            .replace("InstallSize=120", "InstallSize=540")
            + "\nHistory_0.1.1=Index-only section navigation corrections; "
              "original commentary words and source references retained\n"
        ).encode("utf-8")
        args = dict(
            previous_version="0.1.0", proposed_version="0.1.1",
            installed_native_data_size=540
        )
        receipt = verify_private_versioned_commentary_conf_delta(
            source, staged, **args)
        self.assertTrue(receipt["private_metadata_exact_reviewed_delta_only"])
        self.assertTrue(
            receipt["original_distribution_license_textsource_about_and_date_unchanged"])
        self.assertFalse(receipt["public_release_or_new_revision_date_authorized"])
        for tampered in (
            staged.replace(b"Public Domain", b"CC0"),
            staged.replace(b"TextSource=https://example.invalid/source",
                           b"TextSource=https://example.invalid/other"),
            staged.replace(b"SwordVersionDate=2020-02-03",
                           b"SwordVersionDate=2026-11-15"),
            staged.replace(b"About=Source printing assertion",
                           b"About=Certified printed-edition match"),
            staged.replace(b"GlobalOptionFilter=OSISHeadings",
                           b"GlobalOptionFilter=OSISLemma"),
            staged.replace(b"InstallSize=540", b"InstallSize=541"),
            staged.replace(b"History_0.1.1=", b"History_0.1.0="),
            staged.replace(b"Version=0.1.1", b"Version=0.1.0"),
            staged + b"Unapproved=extra\n",
        ):
            with self.subTest(tampered_suffix=tampered[-72:]):
                with self.assertRaises(ValueError):
                    verify_private_versioned_commentary_conf_delta(
                        source, tampered, **args)
        with self.assertRaises(ValueError):
            verify_private_versioned_commentary_conf_delta(
                source, staged, **{**args, "installed_native_data_size":541})
        with self.assertRaises(ValueError):
            verify_private_versioned_commentary_conf_delta(
                source.replace(b"DistributionLicense=Public Domain\n", b""),
                staged, **args)

    def test_private_source_corrected_history_is_explicit_not_index_only(self):
        source = (
            b"[Curated]\nDataPath=./modules/comments/zcom/curated/\n"
            b"ModDrv=zCom\nSourceType=OSIS\nVersification=KJV\n"
            b"BlockType=BOOK\nVersion=0.1.0\nInstallSize=15\n"
            b"DistributionLicense=Public Domain\nTextSource=https://source.invalid/\n"
            b"About=Invented source printing declaration, not independently verified\n"
            b"SwordVersionDate=2020-02-03\n"
        )
        note = "Reviewed index navigation links and one documented source citation correction"
        staged = (
            source.decode("utf-8")
            .replace("BlockType=BOOK", "BlockType=CHAPTER")
            .replace("Version=0.1.0", "Version=0.1.1")
            .replace("InstallSize=15", "InstallSize=16")
            + "\nHistory_0.1.1=" + note + "\n"
        ).encode("utf-8")
        kwargs = dict(
            previous_version="0.1.0", proposed_version="0.1.1",
            installed_native_data_size=16, history_note=note,
            source_reference_change_verified=True,
        )
        receipt = verify_private_versioned_commentary_conf_delta(
            source, staged, **kwargs)
        self.assertTrue(receipt["private_metadata_exact_reviewed_delta_only"])
        self.assertTrue(receipt["private_source_reference_change_verified"])
        self.assertTrue(
            receipt["original_distribution_license_textsource_about_and_date_unchanged"])
        self.assertFalse(receipt["public_release_or_new_revision_date_authorized"])
        for corrupted in (
            staged.replace(b"Public Domain", b"CC0"),
            staged.replace(b"Date=2020-02-03", b"Date=2026-11-15"),
            staged.replace(note.encode("utf-8"), b"Index-only section navigation corrections"),
            staged + b"\nIllegalExtra=extra\n",
        ):
            with self.subTest(corrupted=corrupted[-60:]):
                with self.assertRaises(ValueError):
                    verify_private_versioned_commentary_conf_delta(
                        source, corrupted, **kwargs)
        with self.assertRaises(ValueError):
            verify_private_versioned_commentary_conf_delta(
                source, staged, **{**kwargs, "history_note": "Line break\nforged"}
            )
        with self.assertRaises(ValueError):
            verify_private_versioned_commentary_conf_delta(
                source, staged, **{**kwargs, "source_reference_change_verified": None}
            )

    def test_optional_upstream_metadata_is_not_invented(self):
        source = (
            b"[Curated]\nDataPath=./modules/comments/zcom/curated/\n"
            b"ModDrv=zCom\nSourceType=OSIS\nVersification=KJV\n"
            b"BlockType=BOOK\nVersion=0.1.0\nInstallSize=5\n"
            b"DistributionLicense=Public Domain\n"
        )
        staged = (
            source.decode("utf-8")
            .replace("BlockType=BOOK", "BlockType=CHAPTER")
            .replace("Version=0.1.0", "Version=0.1.1")
            .replace("InstallSize=5", "InstallSize=10")
            + "\nHistory_0.1.1=Index-only section navigation corrections; "
              "original commentary words and source references retained\n"
        ).encode("utf-8")
        self.assertTrue(verify_private_versioned_commentary_conf_delta(
            source, staged, previous_version="0.1.0",
            proposed_version="0.1.1", installed_native_data_size=10
        )["private_metadata_exact_reviewed_delta_only"])


class PrivateVersionedCommentaryZipTests(unittest.TestCase):
    def test_private_package_rejects_same_identity_and_invalid_metadata_without_native_side_effects(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            binary=root/"sword-native-raw"
            binary.write_bytes(b"test-only")
            output=root/"scratch"
            output.mkdir()
            args=dict(
                compiler_root=root,compiled_module_id="Probe",
                package_module_id="Curated",previous_version="0.1.0",
                proposed_version="0.1.1",
                published_conf_template=(
                    b"[Curated]\\nDataPath=./modules/comments/zcom/curated/\\n"
                    b"ModDrv=zCom\\nSourceType=OSIS\\nVersification=KJV\\n"
                    b"BlockType=BOOK\\nVersion=0.1.0\\n"
                ).replace(b"\\\\n",b"\\n"),
                scratch=output,native_raw_binary=binary
            )
            with self.assertRaises(ValueError):
                privately_stage_versioned_zcom_zip(
                    **{**args,"compiled_module_id":"Curated"})
            with self.assertRaises(ValueError):
                privately_stage_versioned_zcom_zip(
                    **{**args,"proposed_version":"0.1.0"})
            with self.assertRaises(ValueError):
                privately_stage_versioned_zcom_zip(
                    **{**args,"published_conf_template":b"[Unreviewed]\\nVersion=0.1.0\\n"})
            self.assertEqual(list(output.iterdir()),[])


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

    def test_private_mixed_original_first_verse_alias_preserves_source_raw_without_approval(self):
        original = b'<div><p>Invented commentary; punctuation remains!</p></div>'
        source = [("Gen.36.2", original), ("Gen.36.3", original)]
        proposed = {"Gen.36.1": {
            "link_to": "Gen.36.2",
            "source_raw_sha256": sha256(original).hexdigest(),
        }}
        xml, meta = build_mixed_original_transport(
            "Gen.36", b"<div type='book'/>", b"<div type='chapter'/>",
            source, work_id="MixedAliasTest",
            provisional_index_aliases=proposed,
        )
        root = etree.fromstring(xml)
        self.assertEqual(len(root.xpath(
            "//*[local-name()='div' and @annotateRef='Gen.36.1-Gen.36.3']"
        )), 1)
        self.assertEqual(xml.count(original), 1)
        self.assertEqual(meta["provisional_index_alias_count"], 1)
        self.assertTrue(meta["provisional_index_aliases_not_editorially_approved"])
        self.assertFalse(meta["source_intro_raw_modified"])
        self.assertFalse(meta["source_k_raw_modified"])
        self.assertFalse(meta["source_published"])
        for unsafe in (
            {"Gen.36.2": proposed["Gen.36.1"]},
            {"Gen.37.1": proposed["Gen.36.1"]},
            {"Gen.36.1": {"link_to": "Gen.36.99",
                            "source_raw_sha256": sha256(original).hexdigest()}},
            {"Gen.36.1": {"link_to": "Gen.36.2",
                            "source_raw_sha256": "a"*64}},
        ):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(ValueError):
                    build_mixed_original_transport(
                        "Gen.36", b"<div/>", b"<chapter/>", source,
                        work_id="MixedAliasTest", provisional_index_aliases=unsafe
                    )

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



class NativeLinkedIdentityTests(unittest.TestCase):
    def test_native_pairs_distinguish_nonadjacent_link_from_middle_section(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import subprocess
        with TemporaryDirectory() as td:
            root=Path(td)
            binary=root/"index-inspector";binary.write_bytes(b"not an executable")
            original={
                "Gen.1.1":b"<p>A source section</p>",
                "Gen.1.3":b"<p>An independent middle section</p>",
            }
            aliases={
                "Gen.1.2":{"link_to":"Gen.1.1"},
                "Gen.1.5":{"link_to":"Gen.1.1"},
            }
            observed=[]
            def mock_run(args,**kwargs):
                first,second=args[-2:]
                link=first=="Gen.1.1" and second in ("Gen.1.2","Gen.1.5")
                observed.append((first,second))
                return subprocess.CompletedProcess(args,0,
                    f"L\t{first}\t{second}\t{int(link)}\n".encode())
            with patch("commentary_osis_mixed_transport_probe.subprocess.run",
                       side_effect=mock_run):
                result=probe_native_original_link_identity(
                    installed_candidate_root=root,module_id="ProbeTest",
                    inspector_binary=binary,original_numbered=original,
                    provisional_aliases=aliases
                )
            self.assertEqual(len(observed),3)
            self.assertEqual(result["native_linked_alias_count"],2)
            self.assertTrue(result["all_independently_distinct_section_controls_unlinked"])
            self.assertEqual(result["negative_distinct_section_controls"],1)
            self.assertTrue(result["source_text_and_xml_never_logged"])

    def test_native_link_identity_fails_if_alias_is_only_text_copy(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import subprocess
        with TemporaryDirectory() as td:
            root=Path(td);binary=root/"index-inspector";binary.write_bytes(b"fixture")
            with patch("commentary_osis_mixed_transport_probe.subprocess.run",
                       return_value=subprocess.CompletedProcess(
                         ["probe"],0,b"L\tGen.1.1\tGen.1.5\t0\n"
                       )):
                actual=probe_native_original_link_identity(
                    installed_candidate_root=root,module_id="ProbeTest",
                    inspector_binary=binary,
                    original_numbered={"Gen.1.1":b"<p>Original</p>"},
                    provisional_aliases={"Gen.1.5":{"link_to":"Gen.1.1"}}
                )
        self.assertEqual(actual["non_linked_proposed_pairs"],["Gen.1.5"])
        self.assertFalse(actual["all_original_master_to_proposed_target_pairs_are_native_linked"])


class PrivateCommentarySwordIdRenameTests(unittest.TestCase):
    """Use invented-only data to prevent accidental CrossWire/curated mixing."""

    def setUp(self):
        self.source=(
            b"# Original metadata retained\n"
            b"[BRTEST]\nDescription=Invented commentary\n"
            b"DataPath=./modules/comments/zcom/brtest/\n"
            b"ModDrv=zCom\nSourceType=OSIS\n"
            b"Version=0.1.0\nDistributionLicense=Public Domain\n"
            b"About=Invented original description retained verbatim!\n"
        )

    def test_exact_id_and_data_path_only_change_with_byte_reversal(self):
        revised=private_rekey_sword_commentary_conf(
            self.source, original_module_id="BRTEST",
            replacement_module_id="TEST",
        )
        self.assertIn(b"[TEST]\n", revised)
        self.assertIn(b"DataPath=./modules/comments/zcom/test/\n", revised)
        self.assertNotIn(b"[BRTEST]\n", revised)
        self.assertEqual(
            private_rekey_sword_commentary_conf(
                revised, original_module_id="TEST",
                replacement_module_id="BRTEST",
            ), self.source,
        )
        self.assertIn(b"Original metadata retained", revised)
        self.assertIn(b"DistributionLicense=Public Domain", revised)
        self.assertIn(b"About=Invented original description retained verbatim!", revised)

    def test_identity_transition_fails_closed_for_original_mismatch_and_duplicates(self):
        malformed=[
            self.source.replace(b"[BRTEST]", b"[UNKNOWN]"),
            self.source.replace(b"[BRTEST]", b"[BRTEST]\n[BRTEST]"),
            self.source.replace(b"brtest/", b"somewhere/"),
            self.source.replace(b"ModDrv=zCom", b"ModDrv=RawText"),
            self.source.replace(b"SourceType=OSIS", b"SourceType=Plain"),
            self.source+b"DataPath=./modules/comments/zcom/brtest/\n",
        ]
        for original in malformed:
            with self.subTest(original=original):
                with self.assertRaises(ValueError):
                    private_rekey_sword_commentary_conf(
                        original, original_module_id="BRTEST",
                        replacement_module_id="TEST",
                    )
        for replacement in ("BRTEST", "brtest", "", "../TEST", "TEST\nAbout=No"):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    private_rekey_sword_commentary_conf(
                        self.source, original_module_id="BRTEST",
                        replacement_module_id=replacement,
                    )


if __name__=="__main__":
    unittest.main()
