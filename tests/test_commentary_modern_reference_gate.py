"""Synthetic source-native biblical-link provenance and fail-closed tests."""
import hashlib
import tempfile
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from commentary_modern_reference_gate import (SourceReferenceGate,
    WholeCanonOriginalLinkIdentityReceipt, canonical_only_for_comparison,
    validate_proposed_link_dispositions, _wrap_exact_authored_modern_text,
    _unambiguous_explicit_modern_verse, _auto_single_verse_placements,
    _unrecognized_original_ref_class, _source_same_chapter_verse_range,
    _unambiguous_explicit_modern_range, _allowed_source_link_target,
    _original_reference_table_ownership, _original_reference_title_ownership,
    _source_range_section_ownership)


ORIGINAL=(b'<div><reference osisRef="Bible:1John.5.20">1Jo 5:20</reference>'
          b' and <hi>original exposition</hi></div>')
SOURCE_HASH=hashlib.sha256(ORIGINAL).hexdigest()
FULL_HASH="a"*64


def source():
    return {
        "scope":"Gen.1",
        "verified_entire_native_corpus_sha256":FULL_HASH,
        "sections":[{
            "first_key":"Gen.1.3",
            "source_sha256":SOURCE_HASH,
            "markup_census":{"tag_counts":{"reference":1}}}
        ]
    }


def expected():
    return {"Gen.1.3":[{"canonical_target":"1John.5.20",
                          "modern_text_marker":"(1 John 5:20)"}]}


class OriginalReferenceGateTests(unittest.TestCase):
    def test_original_attributes_and_modern_markers_are_both_checked(self):
        g=SourceReferenceGate(source_map=source(),expected_refs=expected(),
                               candidate="The Son gives understanding (1 John 5:20).")
        g.observe("I","Gen.1",b"<div>an intro not a source section</div>")
        g.observe("K","Gen.1.3",ORIGINAL)
        proof=g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})
        self.assertEqual(proof["original_reference_links_checked"],1)
        self.assertEqual(proof["source_unique_units_checked"],1)
        self.assertFalse(proof["new_modern_osis_reference_targets_embedded"])
        self.assertFalse(proof["original_osisRef_literal_values_exported"])
        self.assertNotIn("1John.5.20",str(proof))

    def test_original_book_and_chapter_introductions_are_separately_attested(self):
        intro=b"<div><title>Chapter 1</title>Source introduction prose.</div>"
        metadata=source()
        metadata["introductions"]=[{
            "native_key":"Gen.1",
            "source_sha256":hashlib.sha256(intro).hexdigest()
        }]
        g=SourceReferenceGate(source_map=metadata,expected_refs=expected(),
                              candidate="(1 John 5:20)")
        g.observe("I","Gen.1",intro)
        g.observe("K","Gen.1.3",ORIGINAL)
        proof=g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})
        self.assertEqual(proof["original_intro_units_found"],1)
        self.assertEqual(proof["per_intro_unit"]["Gen.1"]["source_visible_word_count"],5)
        self.assertTrue(proof["per_intro_unit"]["Gen.1"]["has_visible_text"])
        self.assertNotIn("Source introduction prose",str(proof))

    def test_missing_original_introduction_blocks_complete_proof(self):
        intro=b"<div>Source introduction</div>"
        metadata=source()
        metadata["introductions"]=[{
            "native_key":"Gen.1",
            "source_sha256":hashlib.sha256(intro).hexdigest()
        }]
        g=SourceReferenceGate(source_map=metadata,expected_refs=expected(),
                              candidate="(1 John 5:20)")
        g.observe("K","Gen.1.3",ORIGINAL)
        with self.assertRaisesRegex(ValueError,"introduction"):
            g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})

    def test_compound_original_first_K_owns_book_intro_and_outline_not_empty_I(self):
        raw=(b'<div><title>Chapter Outline</title>'
             b'Genesis was written under inspiration.'
             b'<table><row><cell>Creation</cell><cell>1-2</cell></row></table>'
             b'The first verse gives an account of Creation.'
             b'<reference osisRef="Bible:1John.5.20">1Jo</reference></div>')
        orig_intro=b"<div/>"
        meta=source()
        meta["sections"][0]["source_sha256"]=hashlib.sha256(raw).hexdigest()
        meta["sections"][0]["markup_census"]["tag_counts"]["reference"]=1
        meta["introductions"]=[{
            "native_key":"Gen",
            "source_sha256":hashlib.sha256(orig_intro).hexdigest()
        }]
        meta["intro_provenance_expectations"]={
            "original_first_numbered_key":"Gen.1.3",
            "expected_original_book_intro_start":"Genesis was written under inspiration",
            "expected_original_exposition_start":"The first verse gives an account",
            "expected_original_chapter_outline_table_count":1,
            "expected_original_chapter_outline_row_count":1,
            "expected_original_chapter_outline_title_count":1
        }
        g=SourceReferenceGate(source_map=meta,expected_refs=expected(),
                              candidate="This has (1 John 5:20).")
        g.observe("I","Gen",orig_intro)
        g.observe("K","Gen.1.3",raw)
        proof=g.report({"all_native_raw_entries_ordered_sha256":FULL_HASH})
        self.assertTrue(proof["original_book_intro_and_outline_owned_by_first_numbered_K_attested"])
        self.assertEqual(proof["per_intro_unit"]["Gen"]["source_visible_word_count"],0)
        self.assertFalse(proof["original_prose_or_reference_labels_exported"])

    def test_no_silent_change_of_source_link_destination(self):
        g=SourceReferenceGate(source_map=source(),expected_refs=expected(),
                               candidate="(1 John 5:20)")
        with self.assertRaises(ValueError):
            g.observe("K","Gen.1.3",ORIGINAL.replace(b"5.20",b"5.21"))

    def test_changed_whole_source_blocked(self):
        g=SourceReferenceGate(source_map=source(),expected_refs=expected(),
                               candidate="(1 John 5:20)")
        g.observe("K","Gen.1.3",ORIGINAL)
        with self.assertRaisesRegex(ValueError,"Whole native source changed"):
            g.report({"all_native_raw_entries_ordered_sha256":"b"*64})

    def test_missing_modern_text_reference_blocked(self):
        with self.assertRaisesRegex(ValueError,"not retained"):
            SourceReferenceGate(source_map=source(),expected_refs=expected(),
                                candidate="The Son grants understanding.")

    def test_every_native_section_requires_explicit_expectation(self):
        with self.assertRaisesRegex(ValueError,"Every source section"):
            SourceReferenceGate(source_map=source(),expected_refs={},
                                candidate="(1 John 5:20)")

    def test_ambiguous_source_links_fail(self):
        for val in ("Bible:Gen.1", "x,y", "unknown", "", "Bible:Ps.0.0"):
            with self.subTest(value=val):
                with self.assertRaises(ValueError):
                    canonical_only_for_comparison(val)


def whole_source_receipt(*, reference_count=1):
    return {
        "status": "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL",
        "original_compiled_corpus_sha256": FULL_HASH,
        "source_prose_or_original_markup_exported": False,
        "semantic_translation_independently_approved": False,
        "chapters": {
            "Gen.1": {
                "original_units": [{
                    "first_key": "Gen.1.3",
                    "keys": ["Gen.1.3", "Gen.1.4"],
                    "source_unit_sha256": SOURCE_HASH,
                    "markup": {
                        "strict_xml_fragment": True,
                        "tag_counts": {"reference": reference_count}
                    }
                }]
            }
        }
    }


class WholeNativeReferenceIdentityTests(unittest.TestCase):
    def test_exact_link_and_label_hashes_are_private_and_ordered(self):
        gate = WholeCanonOriginalLinkIdentityReceipt(whole_source_receipt())
        gate.observe("I", "Gen.1", b"<div>unrelated introduction</div>")
        gate.observe("K", "Gen.1.3", ORIGINAL)
        gate.observe("K", "Gen.1.4", ORIGINAL)
        report = gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        self.assertEqual(report["original_numbered_K_keys_verified"], 2)
        self.assertEqual(report["original_unique_K_bodies_verified"], 1)
        self.assertEqual(report["original_reference_elements_verified"], 1)
        self.assertEqual(report["original_link_bearing_K_bodies"], 1)
        group = report["source_link_groups"][0]
        self.assertEqual(group["source_raw_sha256"], SOURCE_HASH)
        self.assertEqual(group["original_osisRef_sha256_in_document_order"],
                         [hashlib.sha256(b"Bible:1John.5.20").hexdigest()])
        self.assertEqual(group["original_visible_link_label_sha256_in_document_order"],
                         [hashlib.sha256(b"1Jo 5:20").hexdigest()])
        self.assertNotIn("Bible:1John.5.20", str(report))
        self.assertNotIn("1Jo 5:20", str(report))
        self.assertFalse(report["modern_osisRef_targets_or_order_verified"])
        self.assertFalse(report["modern_module_built_or_published"])

    def test_complex_original_link_target_is_hashed_not_normalized(self):
        raw = (b'<div><reference osisRef="Bible:Gen.1.1-Gen.1.3">'
               b'original linked label</reference></div>')
        receipt = whole_source_receipt()
        receipt["chapters"]["Gen.1"]["original_units"][0][
            "source_unit_sha256"] = hashlib.sha256(raw).hexdigest()
        gate = WholeCanonOriginalLinkIdentityReceipt(receipt)
        gate.observe("K", "Gen.1.3", raw)
        gate.observe("K", "Gen.1.4", raw)
        report = gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        self.assertEqual(report["source_link_groups"][0][
            "original_osisRef_sha256_in_document_order"], [
                hashlib.sha256(b"Bible:Gen.1.1-Gen.1.3").hexdigest()])
        self.assertFalse(report["original_source_prose_or_XML_exported"])

    def test_repeated_original_target_and_label_remain_two_occurrences(self):
        # Repeated authorial link elements must not be deduplicated simply
        # because the literal destination and displayed labels are identical.
        raw = (b'<div><reference osisRef="Bible:Gen.1.1">the same label</reference> '
               b'and <reference osisRef="Bible:Gen.1.1">the same label</reference></div>')
        receipt = whole_source_receipt(reference_count=2)
        receipt["chapters"]["Gen.1"]["original_units"][0][
            "source_unit_sha256"] = hashlib.sha256(raw).hexdigest()
        gate = WholeCanonOriginalLinkIdentityReceipt(receipt)
        gate.observe("K", "Gen.1.3", raw)
        gate.observe("K", "Gen.1.4", raw)
        result = gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        group = result["source_link_groups"][0]
        self.assertEqual(result["original_reference_elements_verified"], 2)
        self.assertEqual(group["reference_count"], 2)
        self.assertEqual(len(group["original_osisRef_sha256_in_document_order"]), 2)
        self.assertEqual(len(set(group["original_osisRef_sha256_in_document_order"])), 1)
        self.assertEqual(len(set(
            group["original_visible_link_label_sha256_in_document_order"])), 1)

    def test_missing_or_corrupt_original_aliases_fail_closed(self):
        gate = WholeCanonOriginalLinkIdentityReceipt(whole_source_receipt())
        gate.observe("K", "Gen.1.3", ORIGINAL)
        with self.assertRaisesRegex(ValueError, "not completely read"):
            gate.report({"all_native_raw_entries_ordered_sha256": FULL_HASH})
        with self.assertRaisesRegex(ValueError, "source SHA differ"):
            gate.observe("K", "Gen.1.4", ORIGINAL.replace(b"5.20", b"5.21"))
        gate.observe("K", "Gen.1.4", ORIGINAL)
        with self.assertRaisesRegex(ValueError, "SHA does not match"):
            gate.report({"all_native_raw_entries_ordered_sha256": "b" * 64})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            gate.observe("K", "Gen.1.4", ORIGINAL)

    def test_source_reference_count_drift_and_missing_osisref_are_rejected(self):
        wrong_census = WholeCanonOriginalLinkIdentityReceipt(
            whole_source_receipt(reference_count=2))
        with self.assertRaisesRegex(ValueError, "reference count"):
            wrong_census.observe("K", "Gen.1.3", ORIGINAL)

        raw = b"<div><reference>original label without destination</reference></div>"
        source = whole_source_receipt()
        source["chapters"]["Gen.1"]["original_units"][0][
            "source_unit_sha256"] = hashlib.sha256(raw).hexdigest()
        gate = WholeCanonOriginalLinkIdentityReceipt(source)
        with self.assertRaisesRegex(ValueError, "missing/unsafe"):
            gate.observe("K", "Gen.1.3", raw)

    def test_duplicate_key_in_source_receipt_is_rejected(self):
        receipt = whole_source_receipt()
        receipt["chapters"]["Gen.1"]["original_units"][0]["keys"].append("Gen.1.4")
        with self.assertRaisesRegex(ValueError, "Repeated"):
            WholeCanonOriginalLinkIdentityReceipt(receipt)


def correction_fixture(root: Path):
    raw = b'<div><reference osisRef="2Cor.6.2">2</reference></div>'
    digest = hashlib.sha256(raw).hexdigest()
    chapter = "Gen.2"
    path = "work/mhcc-modern/production/accepted/genesis-02.md"
    output = root / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        '---\nchapter_osis: "Gen.2"\nsource_native_corpus_sha256: "' +
        FULL_HASH + '"\npublication_status: "NOT RELEASED"\n---\n'
        '# Genesis 2\n\n## Two trees (verses 8–9)\n'
        'Second, the tree of knowledge. (Revelation 22:2)\n'
        '\n---\n## Editorial notes\n', encoding="utf-8")
    manifest = {
        "status": "SECONDARY_WITNESS_LINK_CORRECTION_PROPOSALS_NOT_EDITORIAL_RELEASE_APPROVAL",
        "source_module": "MHCC 0.1.1",
        "source_native_corpus_sha256": FULL_HASH,
        "explicit_owner_publication_authorization": False,
        "independent_original_semantic_signoff": False,
        "modern_sword_compiled_or_published": False,
        "cases": [{
            "chapter": chapter,
            "source_first_key": "Gen.2.8",
            "source_unit_sha256": digest,
            "modern_path": path,
            "modern_section_heading": "Two trees (verses 8–9)",
            "witness_url": "https://example.org/authorial-primary-witness",
            "corrections": [{
                "source_link_ordinal": 1,
                "original_target": "2Cor.6.2",
                "original_label": "2",
                "disposition": "OMIT_SPURIOUS_ENUMERATOR_LINK",
                "modern_context_anchor": "Second, the tree of knowledge."
            }],
            "modern_witness_links": [{
                "target": "Rev.22.2",
                "modern_text_marker": "(Revelation 22:2)",
                "disposition":
                    "ADD_SECONDARY_WITNESS_AUTHORED_REFERENCE_NOT_IN_NATIVE_LINKS"
            }]
        }]
    }
    native = {
        "status": "SOURCE_NATIVE_RECEIPT_ONLY_NOT_TRANSLATION_APPROVAL",
        "original_compiled_corpus_sha256": FULL_HASH,
        "source_prose_or_original_markup_exported": False,
        "chapters": {"Gen.2": {
            "original_units": [{
                "first_key": "Gen.2.8",
                "keys": ["Gen.2.8", "Gen.2.9"],
                "source_unit_sha256": digest
            }]
        }}
    }
    ids = {
        "status": WholeCanonOriginalLinkIdentityReceipt.STATUS,
        "whole_native_source_sha256": FULL_HASH,
        "original_link_destinations_only_sha256_not_exported": True,
        "original_visible_link_text_only_sha256_not_exported": True,
        "original_source_prose_or_XML_exported": False,
        "original_numbered_K_keys_verified": 28742,
        "original_unique_K_bodies_verified": 4047,
        "original_reference_elements_verified": 1204,
        "original_link_bearing_K_bodies": 1,
        "source_link_groups": [{
            "first_key": "Gen.2.8",
            "source_raw_sha256": digest,
            "reference_count": 1,
            "original_osisRef_sha256_in_document_order": [
                hashlib.sha256(b"2Cor.6.2").hexdigest()
            ],
            "original_visible_link_label_sha256_in_document_order": [
                hashlib.sha256(b"2").hexdigest()
            ]
        }]
    }
    return manifest, native, ids


class ProposedLinkDispositionTests(unittest.TestCase):
    def test_bounded_original_source_and_modern_section_both_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, native, ids = correction_fixture(root)
            report = validate_proposed_link_dispositions(
                manifest=manifest, native=native, identities=ids,
                repository_root=root)
            self.assertEqual(report["source_links_proposed_to_omit"], 1)
            self.assertEqual(report["secondary_witness_links_proposed_to_add"], 1)
            self.assertEqual(report["reviewed_source_link_groups"], 1)
            self.assertFalse(report["derived_SWORD_link_placements_or_native_readbacks_tested"])
            self.assertFalse(report["release_authorized"])

    def test_mismatch_missing_modern_marker_and_unreviewed_status_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, native, ids = correction_fixture(root)
            case = manifest["cases"][0]
            case["corrections"][0]["original_target"] = "2Cor.6.3"
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                validate_proposed_link_dispositions(
                    manifest=manifest, native=native, identities=ids,
                    repository_root=root)
            case["corrections"][0]["original_target"] = "2Cor.6.2"
            case["modern_witness_links"][0]["modern_text_marker"] = "(Not in manuscript)"
            with self.assertRaisesRegex(ValueError, "not tied"):
                validate_proposed_link_dispositions(
                    manifest=manifest, native=native, identities=ids,
                    repository_root=root)
            case["modern_witness_links"][0]["modern_text_marker"] = "(Revelation 22:2)"
            manifest["explicit_owner_publication_authorization"] = True
            with self.assertRaisesRegex(ValueError, "release signoff"):
                validate_proposed_link_dispositions(
                    manifest=manifest, native=native, identities=ids,
                    repository_root=root)

    def test_no_scope_change_or_duplicate_source_link_ordinal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, native, ids = correction_fixture(root)
            case = manifest["cases"][0]
            case["modern_section_heading"] = "Two trees (verses 8–10)"
            with self.assertRaisesRegex(ValueError, "heading not uniquely"):
                validate_proposed_link_dispositions(
                    manifest=manifest, native=native, identities=ids,
                    repository_root=root)
            case["modern_section_heading"] = "Two trees (verses 8–9)"
            case["corrections"].append(dict(case["corrections"][0]))
            with self.assertRaisesRegex(ValueError, "duplicated"):
                validate_proposed_link_dispositions(
                    manifest=manifest, native=native, identities=ids,
                    repository_root=root)


class BoundedOriginalSourceLinkInsertionTests(unittest.TestCase):
    NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"

    def test_same_modern_wording_after_bounded_cross_reference_injection(self):
        ns=self.NS
        section=ET.Element(f"{{{ns}}}div",{"annotateType":"commentary"})
        para=ET.SubElement(section,f"{{{ns}}}p")
        para.text="The Savior is truly our brother (Hebrews 2:11, 14), and is risen."
        before="".join(section.itertext())
        _wrap_exact_authored_modern_text(
            section,anchor="(Hebrews 2:11, 14)",display="14",
            occurrence="last",target="Heb.2.14")
        self.assertEqual("".join(section.itertext()),before)
        link=section.find(f".//{{{ns}}}reference")
        self.assertIsNotNone(link)
        self.assertEqual(link.attrib["osisRef"],"Heb.2.14")
        self.assertEqual(link.text,"14")
        self.assertEqual(len(section.findall(f".//{{{ns}}}reference")),1)
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):
            _wrap_exact_authored_modern_text(
                section,anchor="(Hebrews 2:11, 14)",display="14",
                occurrence="last",target="Heb.2.14")

    def test_original_literal_osisRef_and_modern_full_citation_survive(self):
        ns=self.NS
        section=ET.Element(f"{{{ns}}}div")
        para=ET.SubElement(section,f"{{{ns}}}p")
        para.text="God is revealed (1 John 5:20)."
        original="".join(section.itertext())
        _wrap_exact_authored_modern_text(
            section,anchor="(1 John 5:20)",display="(1 John 5:20)",
            occurrence="last",target="Bible:1John.5.20")
        self.assertEqual("".join(section.itertext()),original)
        self.assertEqual(section.find(f".//{{{ns}}}reference").get("osisRef"),
                         "Bible:1John.5.20")

    def test_bold_markdown_citation_and_tail_after_highlight_are_linked(self):
        ns=self.NS
        section=ET.Element(f"{{{ns}}}div")
        para=ET.SubElement(section,f"{{{ns}}}p")
        para.text="The apostle calls for prayer ("
        bold=ET.SubElement(para,f"{{{ns}}}hi",{"type":"bold"})
        bold.text="1 Timothy 2:1–2"
        bold.tail="). He points us to God (Revelation 1:5–6)."
        original="".join(section.itertext())
        _wrap_exact_authored_modern_text(
            section,anchor="1 Timothy 2:1–2",display="2",
            occurrence="last",target="1Tim.2.2")
        self.assertEqual("".join(section.itertext()),original)
        self.assertEqual(bold.find(f"{{{ns}}}reference").text,"2")
        _wrap_exact_authored_modern_text(
            section,anchor="(Revelation 1:5–6)",display="6",
            occurrence="last",target="Rev.1.6")
        self.assertEqual("".join(section.itertext()),original)
        links=section.findall(f".//{{{ns}}}reference")
        self.assertEqual([x.get("osisRef") for x in links],
                         ["1Tim.2.2","Rev.1.6"])

    def test_absent_ambiguous_and_fuzzy_markers_rejected_without_guessing(self):
        ns=self.NS
        section=ET.Element(f"{{{ns}}}div")
        for line in ("(Hebrews 2:11, 14)", "(Hebrews 2:11, 14)"):
            ET.SubElement(section,f"{{{ns}}}p").text=line
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):
            _wrap_exact_authored_modern_text(
                section,anchor="(Hebrews 2:11, 14)",display="14",
                occurrence="last",target="Heb.2.14")
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):
            _wrap_exact_authored_modern_text(
                section,anchor="(Revelation 3:1)",display="1",
                occurrence="last",target="Rev.3.1")
        with self.assertRaises(ValueError):
            _wrap_exact_authored_modern_text(
                section,anchor="(Hebrews 2:11, 14)",display="14",
                occurrence="last",target="not-a-bible-osisref")


class ExactSingleVerseSourceConcordanceTests(unittest.TestCase):
    NS="http://www.bibletechnologies.net/2003/OSIS/namespace"

    def section(self,*paragraphs):
        node=ET.Element(f"{{{self.NS}}}div",{
            "annotateType":"commentary","annotateRef":"Gen.2.1-Gen.2.2"})
        for value in paragraphs:
            ET.SubElement(node,f"{{{self.NS}}}p").text=value
        return node

    def test_named_single_verse_and_numbered_book_are_unique(self):
        n=self.section("He remembers (John 3:16).", "And (1 John 3:16).")
        self.assertEqual(_unambiguous_explicit_modern_verse(n,"John.3.16"),
                         "John 3:16")
        self.assertEqual(_unambiguous_explicit_modern_verse(n,"1John.3.16"),
                         "1 John 3:16")
        n=self.section("The apostles (1 John 3:16).")
        self.assertIsNone(_unambiguous_explicit_modern_verse(n,"John.3.16"))

    def test_repeated_or_ambiguous_labels_do_not_auto_map(self):
        for values in (
            ("Look at John 3:16 and John 3:16.",),
            ("A whole range (John 3:16–17) is cited.",),
            ("A comma range (John 3:16, 17) is cited.",),
            ("A short reference (Jn 3:16) is cited.",),
            ("A different book (John 3:17) is cited.",),
        ):
            with self.subTest(values=values):
                self.assertIsNone(_unambiguous_explicit_modern_verse(
                    self.section(*values),"John.3.16"))

    def test_existing_inline_links_do_not_match_themselves(self):
        n=self.section("The Father loved the world (John 3:16).")
        _wrap_exact_authored_modern_text(
            n,anchor="John 3:16",display="John 3:16",
            target="Bible:John.3.16",occurrence="last")
        self.assertIsNone(_unambiguous_explicit_modern_verse(n,"John.3.16"))

    def test_expository_bold_name_and_two_aliases(self):
        n=self.section("A psalm reminds us that (Psalm 23:1).")
        self.assertEqual(_unambiguous_explicit_modern_verse(n,"Ps.23.1"),
                         "Psalm 23:1")
        n=self.section("These words are in Psalms 23:1.")
        self.assertEqual(_unambiguous_explicit_modern_verse(n,"Ps.23.1"),
                         "Psalms 23:1")
        n=self.section("Song of Songs 2:1 directs us to hope.")
        self.assertEqual(_unambiguous_explicit_modern_verse(n,"Song.2.1"),
                         "Song of Songs 2:1")

    def test_conventional_punctuated_abbreviations_match_only_exact_source_verse(self):
        cases = [
            ("Gen. 12:3", "Gen.12.3"),
            ("Exod. 14:21", "Exod.14.21"),
            ("Ps. 23:1", "Ps.23.1"),
            ("Rom. 8:1", "Rom.8.1"),
            ("1 Cor. 5:7", "1Cor.5.7"),
            ("2 Thess. 3:10", "2Thess.3.10"),
            ("1 Jn. 3:16", "1John.3.16"),
            ("Rev. 22:2", "Rev.22.2"),
        ]
        for literal, target in cases:
            with self.subTest(target=target):
                p = self.section("Compare the passage ("+literal+").")
                self.assertEqual(_unambiguous_explicit_modern_verse(p,target),literal)
        self.assertIsNone(_unambiguous_explicit_modern_verse(
            self.section("1 Jn. 3:16 is cited."),"John.3.16"))
        self.assertIsNone(_unambiguous_explicit_modern_verse(
            self.section("Rom 8:1 is not an accepted punctuated alias."),"Rom.8.1"))

    def test_punctuated_abbreviated_ranges_preserve_original_targets(self):
        p=self.section("See Rom. 8:1–4 and 1 Cor. 5:7–8.")
        self.assertEqual(_unambiguous_explicit_modern_range(
            p,"Rom.8.1-Rom.8.4"),"Rom. 8:1–4")
        self.assertEqual(_unambiguous_explicit_modern_range(
            p,"Bible:1Cor.5.7-1Cor.5.8"),"1 Cor. 5:7–8")
        # No inference of a source range from two disjoint citations.
        self.assertIsNone(_unambiguous_explicit_modern_range(
            self.section("Compare Rom. 8:1 and Rom. 8:4."),
            "Rom.8.1-Rom.8.4"))

    def test_original_target_identity_unapproved_or_ambiguous_skips(self):
        import types
        # A miniature, genuine-like one-group inventory. The method must
        # reject bare "2" source enumerators and repeated source targets.
        n=self.section("One cites John 3:16; another cites Matthew 5:9.")
        source={"chapters":{"Gen.2":{"original_units":[{
            "first_key":"Gen.2.1","keys":["Gen.2.1","Gen.2.2"]}]}}}
        originals={"Gen.2.1":[
            ("Bible:John.3.16","John 3:16"),
            ("Matt.5.9","2"),
            ("John.3.16","another source link to John 3:16"),
            ("Matt.5.9-Matt.5.11","Matthew 5:9–11")]}
        docs={"Gen.2":ET.Element(f"{{{self.NS}}}chapter")}
        docs["Gen.2"].append(n)
        candidates,skipped=_auto_single_verse_placements(
            private_original=originals,groups={},modern_chapters=docs,
            native=source,blocked=set(),corrections={})
        self.assertEqual(candidates,[])
        self.assertEqual(skipped["repeated_original_target"],2)
        self.assertEqual(skipped["unverified_or_single_digit_label"],1)
        self.assertEqual(skipped["unsupported_original_reference_syntax"],1)

    def test_corrected_or_already_reviewed_original_link_not_auto_duplicated(self):
        n=self.section("Read John 3:16 and Matthew 5:9.")
        source={"chapters":{"Gen.2":{"original_units":[{
            "first_key":"Gen.2.1","keys":["Gen.2.1","Gen.2.2"]}]}}}
        originals={"Gen.2.1":[("John.3.16","John 3:16"),
                               ("Matt.5.9","Matthew 5:9")]}
        docs={"Gen.2":ET.Element(f"{{{self.NS}}}chapter")}
        docs["Gen.2"].append(n)
        candidates,skipped=_auto_single_verse_placements(
            private_original=originals,groups={},modern_chapters=docs,
            native=source,blocked={("Gen.2.1",1)},
            corrections={("Gen.2.1",2):{}})
        self.assertEqual(candidates,[])
        self.assertEqual(skipped["already_reviewed"],1)
        self.assertEqual(skipped["proposed_original_correction"],1)

    def test_unrecognized_original_osisref_shape_is_classified_not_guessed(self):
        cases={
            "Bible:John.3.16-John.3.18":"full_verse_range",
            "John.3.16-18":"abbreviated_verse_range",
            "John.3.16 John.3.18":"space_joined_verses",
            "John.3.16,John.3.18":"punctuation_joined_verses",
            "John.3.16-Acts.2":"other_range_syntax",
            "Genesis 3":"other_compound_syntax",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(_unrecognized_original_ref_class(value), expected)

    def test_original_link_ancestry_distinguishes_outlines_and_exposition(self):
        fragment=ET.fromstring(
            '<div><table><row><cell>'
            '<reference osisRef="John.3.16-John.3.18">16–18</reference>'
            '</cell></row></table><div>'
            '<reference osisRef="Rom.5.8">Romans 5:8</reference>'
            '<table><row><cell><reference osisRef="Matt.1.2">2</reference>'
            '</cell></row></table></div></div>')
        self.assertEqual(_original_reference_table_ownership(fragment),
                         [True,False,True])
        self.assertEqual(_original_reference_title_ownership(fragment),
                         [False,False,False])

    def test_original_ranges_can_be_inside_a_title_not_a_table(self):
        fragment=ET.fromstring(
            '<div><title>Acts <reference osisRef="Acts.2.1-Acts.2.4">'
            '1–4</reference></title><div><reference osisRef="John.1.1">'
            'John 1:1</reference></div></div>')
        self.assertEqual(_original_reference_title_ownership(fragment),[True,False])
        self.assertEqual(_original_reference_table_ownership(fragment),[False,False])

    def test_full_original_same_chapter_range_and_exact_modern_citation(self):
        source="Bible:John.3.16-John.3.18"
        self.assertEqual(_source_same_chapter_verse_range(source),
                         ("John","3","16","18"))
        self.assertTrue(_allowed_source_link_target(source))
        section=self.section(
            "We read the whole passage in (John 3:16–18), in context.")
        marker=_unambiguous_explicit_modern_range(section,source)
        self.assertEqual(marker,"John 3:16–18")
        before="".join(section.itertext())
        _wrap_exact_authored_modern_text(
            section,anchor=marker,display=marker,occurrence="last",
            target=source)
        self.assertEqual("".join(section.itertext()),before)
        self.assertEqual(section.find(f".//{{{self.NS}}}reference").get("osisRef"),
                         source)

    def test_ambiguous_and_cross_chapter_source_ranges_are_rejected(self):
        for original in ("Bible:John.3.16-John.4.18",
                         "Bible:John.3.16-Rom.3.18",
                         "John.3.18-John.3.16",
                         "John.03.16-John.03.18",
                         "John.3.16-18"):
            with self.subTest(original=original):
                self.assertIsNone(_source_same_chapter_verse_range(original))
        original="Bible:John.3.16-John.3.18"
        for passage in ("John 3:16–18 and John 3:16–18",
                        "John 3:16–18, 19",
                        "1 John 3:16–18",
                        "John 3:16–17",
                        "John 3:16, 18"):
            with self.subTest(passage=passage):
                self.assertIsNone(_unambiguous_explicit_modern_range(
                    self.section(passage),original))

    def test_only_original_exact_source_range_enters_auto_placement(self):
        n=self.section("The words of Jesus (John 3:16–18) teach grace.")
        source={"chapters":{"Gen.2":{"original_units":[{
            "first_key":"Gen.2.1","keys":["Gen.2.1","Gen.2.2"]}]}}}
        original={"Gen.2.1":[("Bible:John.3.16-John.3.18",
                               "John 3:16–18")]}
        modern={"Gen.2":ET.Element(f"{{{self.NS}}}chapter")}
        modern["Gen.2"].append(n)
        candidates,skipped=_auto_single_verse_placements(
            private_original=original,groups={},modern_chapters=modern,
            native=source,blocked=set(),corrections={},include_ranges=True)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["action"],
                         "AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_RANGE")
        self.assertEqual(candidates[0]["modern_anchor"],"John 3:16–18")
        self.assertEqual(candidates[0]["expected_modern_target"],
                         "RANGE:John.3.16-John.3.18")
        candidates,skipped=_auto_single_verse_placements(
            private_original=original,groups={},modern_chapters=modern,
            native=source,blocked=set(),corrections={},include_ranges=False)
        self.assertEqual(candidates,[])
        self.assertEqual(skipped["unsupported_original_reference_syntax"],1)

    def test_exact_original_authorial_range_and_matching_modern_heading(self):
        section=ET.Element(f"{{{self.NS}}}div",{
            "annotateType":"commentary","annotateRef":"Isa.1.1-Isa.1.9"})
        ET.SubElement(section,f"{{{self.NS}}}title",{"type":"sub"}).text=(
            "Judah's corruption (verses 1–9)")
        keys=["Isa.1."+str(v) for v in range(1,10)]
        exact=_source_range_section_ownership(
            literal="Bible:Isa.1.1-Isa.1.9",label="1-9",
            source_chapter="Isa.1",keys=keys,section=section)
        self.assertEqual(exact,{"same_chapter":True,"exact_K_scope":True,
                                "matching_modern_heading":True,
                                "source_label_is_verse_span":True})
        different=_source_range_section_ownership(
            literal="Bible:Isa.1.1-Isa.1.9",label="1–9",
            source_chapter="Jer.1",
            keys=["Jer.1."+str(v) for v in range(1,10)],section=section)
        self.assertFalse(different["exact_K_scope"])
        self.assertFalse(different["matching_modern_heading"])
        partial=_source_range_section_ownership(
            literal="Bible:Isa.1.1-Isa.1.9",label="1–9",
            source_chapter="Isa.1",keys=keys[:-1],section=section)
        self.assertFalse(partial["exact_K_scope"])
        self.assertFalse(partial["matching_modern_heading"])
        self.assertTrue(partial["same_chapter"])
        other=ET.Element(f"{{{self.NS}}}div")
        ET.SubElement(other,f"{{{self.NS}}}title",{"type":"sub"}).text=(
            "A different topic (verses 4–12)")
        mismatch=_source_range_section_ownership(
            literal="Isa.1.1-Isa.1.9",label="1–9",
            source_chapter="Isa.1",keys=keys,section=other)
        self.assertTrue(mismatch["exact_K_scope"])
        self.assertFalse(mismatch["matching_modern_heading"])

    def test_only_one_exact_original_target_is_proposed(self):
        n=self.section("Paul mentions (Romans 3:23), but there is more.")
        source={"chapters":{"Gen.2":{"original_units":[{
            "first_key":"Gen.2.1","keys":["Gen.2.1","Gen.2.2"]}]}}}
        originals={"Gen.2.1":[("Bible:Rom.3.23","Romans 3:23")]}
        docs={"Gen.2":ET.Element(f"{{{self.NS}}}chapter")}
        docs["Gen.2"].append(n)
        candidates,skipped=_auto_single_verse_placements(
            private_original=originals,groups={},modern_chapters=docs,
            native=source,blocked=set(),corrections={})
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["modern_anchor"],"Romans 3:23")
        self.assertEqual(candidates[0]["source_first_key"],"Gen.2.1")
        self.assertEqual(candidates[0]["original_link_ordinal"],1)
        self.assertEqual(candidates[0]["expected_modern_target"],"Rom.3.23")


if __name__=="__main__":
    unittest.main()
