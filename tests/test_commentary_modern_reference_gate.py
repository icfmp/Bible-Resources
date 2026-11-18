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
    _source_range_section_ownership, _source_first_K_outline_row_evidence,
    _find_exact_modern_original_outline_range_cell,
    _unique_authentic_original_visible_label,
    _unplaced_original_link_review_ledger,
    build_private_compact_original_crossrefs,
    build_private_owned_K_heading_range_links,
    build_private_inline_original_reference_index,
    _source_owned_ordered_alignment,
    _original_source_link_contexts, _source_context_unique_paragraph_anchor,
    build_private_contextual_source_note_preview)


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

    def test_source_first_K_navigation_only_matches_unique_exact_outline_row(self):
        ns=self.NS
        modern=ET.Element(f"{{{ns}}}chapter",{"osisID":"Isa.1"})
        intro=ET.SubElement(modern,f"{{{ns}}}div",{"type":"introduction"})
        ET.SubElement(intro,f"{{{ns}}}title").text="Original chapter outline"
        table=ET.SubElement(intro,f"{{{ns}}}table")
        head=ET.SubElement(table,f"{{{ns}}}row")
        for text in ("Original outline","Verses"):
            ET.SubElement(head,f"{{{ns}}}cell").text=text
        for a,b in (("Judah is corrupt","1–9"),
                    ("The Lord exhorts","10–15")):
            row=ET.SubElement(table,f"{{{ns}}}row")
            ET.SubElement(row,f"{{{ns}}}cell").text=a
            ET.SubElement(row,f"{{{ns}}}cell").text=b
        native={"original_units":[{"first_key":"Isa.1.1","keys":[
            "Isa.1."+str(i) for i in range(1,10)]},
            {"first_key":"Isa.1.10","keys":[
                "Isa.1."+str(i) for i in range(10,16)]}]}
        result=_source_first_K_outline_row_evidence(
            literal="Bible:Isa.1.1-Isa.1.9",label="Is. 1:1-9",
            first_key="Isa.1.1",native_chapter=native,modern_chapter=modern)
        self.assertEqual(result,{
            "source_first_K_owns_link":True,
            "unique_modern_outline_row_matches_source_target":True,
            "original_visible_label_explicitly_names_same_verse_span":True})
        later=_source_first_K_outline_row_evidence(
            literal="Bible:Isa.1.10-Isa.1.15",label="Is. 1:10-15",
            first_key="Isa.1.10",native_chapter=native,modern_chapter=modern)
        self.assertFalse(later["source_first_K_owns_link"])
        corrupted_label=_source_first_K_outline_row_evidence(
            literal="Bible:Isa.1.1-Isa.1.9",label="Is. 1:1-10",
            first_key="Isa.1.1",native_chapter=native,modern_chapter=modern)
        self.assertTrue(corrupted_label["unique_modern_outline_row_matches_source_target"])
        self.assertFalse(corrupted_label["original_visible_label_explicitly_names_same_verse_span"])
        duplicate=ET.SubElement(table,f"{{{ns}}}row")
        ET.SubElement(duplicate,f"{{{ns}}}cell").text="Different"
        ET.SubElement(duplicate,f"{{{ns}}}cell").text="1–9"
        ambiguous=_source_first_K_outline_row_evidence(
            literal="Bible:Isa.1.1-Isa.1.9",label="Is. 1:1-9",
            first_key="Isa.1.1",native_chapter=native,modern_chapter=modern)
        self.assertFalse(ambiguous["unique_modern_outline_row_matches_source_target"])

    def test_original_first_K_full_chapter_outline_links_are_not_prose_crossrefs(self):
        ns=self.NS
        chapter=ET.Element(f"{{{ns}}}chapter",{"osisID":"Isa.1"})
        intro=ET.SubElement(chapter,f"{{{ns}}}div",{"type":"introduction"})
        ET.SubElement(intro,f"{{{ns}}}title").text="Original chapter outline"
        table=ET.SubElement(intro,f"{{{ns}}}table")
        for left,right in (("Original outline","Verses"),
                           ("Corruption","1–9"),("Repentance","10–15")):
            row=ET.SubElement(table,f"{{{ns}}}row")
            ET.SubElement(row,f"{{{ns}}}cell").text=left
            ET.SubElement(row,f"{{{ns}}}cell").text=right
        units=[]
        for start,end in ((1,9),(10,15)):
            keys=["Isa.1."+str(i) for i in range(start,end+1)]
            units.append({"first_key":keys[0],"keys":keys})
            unit=ET.SubElement(chapter,f"{{{ns}}}div",{
                "annotateType":"commentary",
                "annotateRef":keys[0]+"-"+keys[-1]})
            ET.SubElement(unit,f"{{{ns}}}p").text="Authorial modern prose."
        source={"chapters":{"Isa.1":{"original_units":units}}}
        original={"Isa.1.1":[
            ("Bible:Isa.1.1-Isa.1.9","Is. 1:1-9"),
            ("Bible:Isa.1.10-Isa.1.15","Is. 1:10-15")]}
        modern={"Isa.1":chapter}
        candidates,counts=_auto_single_verse_placements(
            private_original=original,groups={},modern_chapters=modern,
            native=source,blocked=set(),corrections={},
            include_ranges=True,include_outline_links=True)
        self.assertEqual(len(candidates),2)
        self.assertEqual([c["action"] for c in candidates],[
            "AUTO_ORIGINAL_FIRST_K_CHAPTER_OUTLINE_RANGE"]*2)
        self.assertEqual([c["modern_anchor"] for c in candidates],
                         ["1–9","10–15"])
        cell=_find_exact_modern_original_outline_range_cell(
            chapter,"Bible:Isa.1.10-Isa.1.15")
        self.assertIsNotNone(cell)
        before="".join(chapter.itertext())
        _wrap_exact_authored_modern_text(
            cell,anchor="10–15",display="10–15",occurrence="last",
            target="Bible:Isa.1.10-Isa.1.15")
        self.assertEqual("".join(chapter.itertext()),before)
        self.assertEqual(cell.find(f"./{{{ns}}}reference").get("osisRef"),
                         "Bible:Isa.1.10-Isa.1.15")
        without,skips=_auto_single_verse_placements(
            private_original=original,groups={},modern_chapters=modern,
            native=source,blocked=set(),corrections={},
            include_ranges=True,include_outline_links=False)
        self.assertEqual(without,[])

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

    def test_original_printed_abbreviation_unique_and_source_attested(self):
        n=self.section("The apostle points us to Rom. 3:23.")
        match=_unique_authentic_original_visible_label(
            n,"Bible:Rom.3.23","Rom. 3:23")
        self.assertEqual(match,"Rom. 3:23")
        prior="".join(n.itertext())
        _wrap_exact_authored_modern_text(
            n,anchor=match,display=match,occurrence="last",
            target="Bible:Rom.3.23")
        self.assertEqual("".join(n.itertext()),prior)
        self.assertEqual(
            n.find(f".//{{{self.NS}}}reference").get("osisRef"),
            "Bible:Rom.3.23")

    def test_original_printed_label_fallback_refuses_wrong_target_and_ambiguity(self):
        cases=(
            ("We read Rom. 3:23.","Bible:Rom.3.24","Rom. 3:23"),
            ("We read Mark 3:23.","Bible:Rom.3.23","Mark 3:23"),
            ("Rom. 3:23 is clear; Rom. 3:23 is repeated.","Rom.3.23","Rom. 3:23"),
            ("Romans 3:23 is clear.","Rom.3.23","3"),
            ("The old citation Rom. 3:23-24 is used.","Rom.3.23-Rom.3.24","Rom. 3:23-24"),
        )
        for verse,target,source_label in cases:
            with self.subTest(verse=verse,target=target):
                self.assertIsNone(_unique_authentic_original_visible_label(
                    self.section(verse),target,source_label))

    def test_source_label_autolink_requires_explicit_opt_in(self):
        n=self.section("Paul makes this point in Rom 3:23.")
        native={"chapters":{"Gen.2":{"original_units":[{
            "first_key":"Gen.2.1","keys":["Gen.2.1","Gen.2.2"]}]}}}
        refs={"Gen.2.1":[("Bible:Rom.3.23","Rom 3:23")]}
        modern={"Gen.2":ET.Element(f"{{{self.NS}}}chapter")}
        modern["Gen.2"].append(n)
        ordinary,_=_auto_single_verse_placements(
            private_original=refs,groups={},modern_chapters=modern,
            native=native,blocked=set(),corrections={})
        self.assertEqual(ordinary,[])
        fallback,_=_auto_single_verse_placements(
            private_original=refs,groups={},modern_chapters=modern,
            native=native,blocked=set(),corrections={},
            include_authentic_labels=True)
        self.assertEqual(len(fallback),1)
        self.assertEqual(fallback[0]["action"],
                         "AUTO_UNIQUE_AUTHENTIC_ORIGINAL_SINGLE_VERSE_LABEL")
        self.assertEqual(fallback[0]["expected_modern_target"],"Rom.3.23")
        repeated={"Gen.2.1":[("Bible:Rom.3.23","Rom 3:23"),
                             ("Matt.5.3","Rom 3:23")]}
        fallback,_=_auto_single_verse_placements(
            private_original=repeated,groups={},modern_chapters=modern,
            native=native,blocked=set(),corrections={},
            include_authentic_labels=True)
        self.assertEqual(fallback,[])

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


class WholeOriginalSourceLinkLedgerTests(unittest.TestCase):
    def test_source_link_occurrences_have_one_exact_review_disposition(self):
        native={
            "Gen.1.1":[
                ("Bible:John.3.16","John 3:16"),
                ("Bible:Ps.1.1-Ps.1.3","Ps. 1:1-3"),
                ("Matt.5.2","2"),
            ]
        }
        inserted=[{
            "original_source_first_key":"Gen.1.1",
            "original_link_ordinal":1,
            "placement_action":"AUTO_EXACT_SOURCE_TARGET_AND_UNIQUE_MODERN_VERSE",
        },{
            "original_source_first_key":"Gen.1.1",
            "original_link_ordinal":None,
            "placement_action":"ADD_AUTHORED_UNLINKED_SOURCE_WITNESS",
        }]
        corrections={("Gen.1.1",3):{
            "disposition":"OMIT_SPURIOUS_ENUMERATOR_LINK"}}
        ledger=_unplaced_original_link_review_ledger(
            original=native,insertions=inserted,corrections=corrections)
        self.assertEqual(ledger["original_native_reference_elements"],3)
        self.assertEqual(ledger["source_link_occurrences_verified_in_derived_osis"],1)
        self.assertEqual(ledger["source_spurious_link_occurrences_explicitly_omitted"],1)
        self.assertEqual(ledger["source_original_links_still_requiring_placement_review"],1)
        self.assertEqual(ledger["pending"][0]["disposition"],
                         "UNPLACED_SAME_CHAPTER_VERSE_RANGE")
        self.assertEqual(ledger["pending"][0]["source_first_key"],"Gen.1.1")
        self.assertEqual(ledger["pending"][0]["source_reference_ordinal"],2)
        self.assertNotIn("Bible:Ps.1.1",repr(ledger))
        self.assertNotIn("John 3:16",repr(ledger))
        with self.assertRaisesRegex(ValueError,"never applied"):
            _unplaced_original_link_review_ledger(
                original=native,insertions=[],corrections={
                    ("Gen.1.1",1):{"disposition":"RETARGET_VERIFIED_CONTINUATION_REFERENCE"},
                    ("Gen.1.1",3):{"disposition":"OMIT_SPURIOUS_ENUMERATOR_LINK"}})
        with self.assertRaisesRegex(ValueError,"placed twice"):
            _unplaced_original_link_review_ledger(
                original=native,insertions=[inserted[0],inserted[0]],
                corrections=corrections)


    def test_native_context_and_literal_presence_are_metadata_only(self):
        ns = "http://www.bibletechnologies.net/2003/OSIS/namespace"
        ch = ET.Element(f"{{{ns}}}chapter", {"osisID": "Gen.1"})
        section = ET.SubElement(ch, f"{{{ns}}}div", {
            "annotateType": "commentary",
            "annotateRef": "Gen.1.1-Gen.1.2",
        })
        ET.SubElement(section, f"{{{ns}}}p").text = (
            "This author cites John 3:16 and the printed Ps. 1:1-3.")
        original = {"Gen.1.1": [
            ("Bible:John.3.16", "John 3:16"),
            ("Bible:Ps.1.1-Ps.1.3", "Ps. 1:1-3"),
            ("Matt.5.2", "2"),
        ]}
        context = {
            "source_table_ownership": {"Gen.1.1": [False, True, False]},
            "source_title_ownership": {"Gen.1.1": [False, True, False]},
            "modern_chapters": {"Gen.1": ch},
            "native": {"chapters": {"Gen.1": {"original_units": [
                {"first_key": "Gen.1.1", "keys": ["Gen.1.1", "Gen.1.2"]}
            ]}}},
        }
        ledger = _unplaced_original_link_review_ledger(
            original=original, insertions=[], corrections={}, **context)
        self.assertEqual(len(ledger["pending"]), 3)
        self.assertEqual(
            [x["native_markup_location"] for x in ledger["pending"]],
            ["EXPOSITION_OR_OTHER", "TABLE_AND_TITLE", "EXPOSITION_OR_OTHER"])
        self.assertEqual(
            [x["original_target_grammar"] for x in ledger["pending"]],
            ["SINGLE_VERSE", "SAME_CHAPTER_FULL_RANGE", "SINGLE_VERSE"])
        self.assertEqual(
            [x["verbatim_original_label_in_modern_K"] for x in ledger["pending"]],
            ["UNIQUE_VERBATIM", "UNIQUE_VERBATIM",
             "NON_DISTINCTIVE_NOT_SCANNED"])
        self.assertNotIn("John 3:16", repr(ledger))
        self.assertNotIn("Ps. 1:1-3", repr(ledger))
        self.assertNotIn("Bible:John.3.16", repr(ledger))
        # Only one coherent, authenticated provenance tuple is acceptable.
        with self.assertRaisesRegex(ValueError, "complete"):
            _unplaced_original_link_review_ledger(
                original=original, insertions=[], corrections={},
                source_table_ownership=context["source_table_ownership"])
        wrong = dict(context)
        wrong["source_title_ownership"] = {"Gen.1.1": [True]}
        with self.assertRaisesRegex(ValueError, "ancestry"):
            _unplaced_original_link_review_ledger(
                original=original, insertions=[], corrections={}, **wrong)
        wrong = dict(context)
        wrong["native"] = {"chapters": {"Gen.1": {"original_units": [
            {"first_key": "Gen.1.1", "keys": ["Gen.1.1"]}
        ]}}}
        with self.assertRaisesRegex(ValueError, "ownership"):
            _unplaced_original_link_review_ledger(
                original=original, insertions=[], corrections={}, **wrong)

    def test_printed_label_diagnostic_never_invents_source_reference(self):
        from commentary_modern_reference_gate import _original_label_in_modern_k
        ns = "http://www.bibletechnologies.net/2003/OSIS/namespace"
        section = ET.Element(f"{{{ns}}}div")
        ET.SubElement(section, f"{{{ns}}}p").text = (
            "John 3:16 and then again John 3:16. John 3:161 is different.")
        self.assertEqual(
            _original_label_in_modern_k(section, "John 3:16"),
            "REPEATED_NOT_UNIQUE")
        self.assertEqual(
            _original_label_in_modern_k(section, "John 3:17"),
            "ABSENT_VERBATIM")
        self.assertEqual(
            _original_label_in_modern_k(section, "16"),
            "NON_DISTINCTIVE_NOT_SCANNED")
        section.clear()
        para = ET.SubElement(section, f"{{{ns}}}p")
        para.text = "Read "
        link = ET.SubElement(para, f"{{{ns}}}reference", {
            "osisRef": "Bible:John.3.16"})
        link.text = "John 3:16"
        link.tail = " and 1 John 3:16 in context."
        self.assertEqual(
            _original_label_in_modern_k(section, "John 3:16"),
            "ABSENT_VERBATIM")


    def test_two_endpoint_native_range_rejection_classes_are_not_links(self):
        from commentary_modern_reference_gate import (
            _full_endpoint_source_range_rejection,
            _source_same_chapter_verse_range)
        examples = {
            "Jer.50.1-Jer.51.5": "CROSS_CHAPTER_RANGE",
            "Exod.13.2-Deut.11.21": "CROSS_BOOK_RANGE",
            "Bible:Isa.35.8-Isa.35.8": "DEGENERATE_SAME_VERSE_RANGE",
            "Jer.50.7-Jer.50.3": "REVERSED_SAME_CHAPTER_RANGE",
            "Ps.01.1-Ps.01.5": "ZERO_OR_NONCANONICAL_NUMERIC_SPELLING",
            "Ps.119.1-Ps.119.201": "OUTSIDE_BOUNDED_VERSE_RANGE",
            "Bogus.2.1-Bogus.2.8": "UNRECOGNIZED_BOOK_CODE",
            "Gen.1.1": "NOT_TWO_ENDPOINT_RANGE",
            "Bible:Jer.50.1-Jer.50.7":
                "VALID_SAME_CHAPTER_RANGE_UNEXPECTEDLY_UNPLACED",
        }
        for literal, expected in examples.items():
            with self.subTest(expected=expected):
                self.assertEqual(
                    _full_endpoint_source_range_rejection(literal), expected)
                if expected not in (
                        "VALID_SAME_CHAPTER_RANGE_UNEXPECTEDLY_UNPLACED",):
                    self.assertIsNone(_source_same_chapter_verse_range(literal))

    def test_unsupported_native_range_has_a_reversible_private_locator(self):
        ns = "http://www.bibletechnologies.net/2003/OSIS/namespace"
        chapter = ET.Element(f"{{{ns}}}chapter", {"osisID": "Jer.50"})
        section = ET.SubElement(chapter, f"{{{ns}}}div", {
            "annotateType": "commentary", "annotateRef": "Jer.50.1"})
        ET.SubElement(section, f"{{{ns}}}p").text = (
            "The prophecy concerns Babylon and the restoration of Israel.")
        original = {"Jer.50.1": [
            ("Bible:Jer.50.1-Jer.51.5", "Jer. 50–51")]}
        ledger = _unplaced_original_link_review_ledger(
            original=original, insertions=[], corrections={},
            source_table_ownership={"Jer.50.1": [False]},
            source_title_ownership={"Jer.50.1": [False]},
            modern_chapters={"Jer.50": chapter},
            native={"chapters": {"Jer.50": {"original_units": [{
                "first_key": "Jer.50.1", "keys": ["Jer.50.1"]}]}}})
        self.assertEqual(
            ledger["source_original_links_still_requiring_placement_review"], 1)
        row = ledger["pending"][0]
        self.assertEqual(row["source_first_key"], "Jer.50.1")
        self.assertEqual(row["source_reference_ordinal"], 1)
        self.assertEqual(row["original_target_grammar"], "full_verse_range")
        self.assertEqual(row["full_range_rejection_reason"],
                         "CROSS_CHAPTER_RANGE")
        self.assertEqual(row["native_markup_location"], "EXPOSITION_OR_OTHER")
        self.assertNotIn("Jer.50.1-Jer.51.5", repr(ledger))
        self.assertNotIn("Jer. 50–51", repr(ledger))


    def test_source_pin_verified_pending_errata_are_never_applied(self):
        from copy import deepcopy
        from commentary_modern_reference_gate import (
            validate_pending_source_reference_errata)
        target = "Jer.50.1-Jer.3.8"
        digest = hashlib.sha256(target.encode()).hexdigest()
        label_hash = hashlib.sha256(b"original printed citation").hexdigest()
        native = {
            "original_compiled_corpus_sha256": "a" * 64,
            "chapters": {"Jer.50": {"original_units": [{
                "first_key": "Jer.50.1",
                "source_unit_sha256": "b" * 64
            }]}}
        }
        ledger = {
            "status":
                "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
            "source_reference_labels_or_literal_targets_exported": False,
            "publication_authorized": False,
            "pending": [{
                "source_first_key": "Jer.50.1",
                "source_reference_ordinal": 1,
                "original_osisRef_sha256": digest,
                "original_visible_label_sha256": label_hash,
                "full_range_rejection_reason": "CROSS_CHAPTER_RANGE",
            }],
        }
        case = {
            "source_first_key": "Jer.50.1",
            "original_native_unit_sha256": "b" * 64,
            "original_reference_ordinal": 1,
            "original_target": target,
            "original_target_sha256": digest,
            "original_visible_label_sha256": label_hash,
            "finding": "INVALID_CROSS_CHAPTER_NAVIGATION_IN_ORIGINAL_OSISREF",
            "candidate_fragment": "Jer.50.1-Jer.50.3",
            "approval": False,
        }
        manifest = {
            "status": "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
            "original_source": "MHCC 0.1.1 SWORD",
            "original_native_corpus_sha256": "a" * 64,
            "original_sword_changed": False,
            "modern_prose_changed": False,
            "modern_osis_links_automatically_changed": False,
            "editorial_target_corrections_approved": False,
            "redistributed": False,
            "cases": [case],
        }
        receipt = validate_pending_source_reference_errata(
            manifest=manifest, ledger=ledger, native=native)
        self.assertEqual(
            receipt["status"],
            "SOURCE_PINNED_PROPOSALS_VERIFIED_NOT_APPLIED_OR_APPROVED")
        self.assertEqual(receipt["source_link_edits_applied"], 0)
        self.assertNotIn(target, repr(receipt))
        for mutate in (
            lambda x: x["cases"][0].update(
                {"original_target": "Jer.50.1-Jer.50.4"}),
            lambda x: x["cases"][0].update(
                {"candidate_fragment": "Jer.50.1-Jer.51.4"}),
            lambda x: x["cases"][0].update(
                {"original_native_unit_sha256": "c" * 64}),
            lambda x: x.update({"editorial_target_corrections_approved": True}),
            lambda x: x["cases"].append(deepcopy(case)),
        ):
            bad = deepcopy(manifest)
            mutate(bad)
            with self.assertRaises(ValueError):
                validate_pending_source_reference_errata(
                    manifest=bad, ledger=ledger, native=native)

    def test_source_pin_wrong_verse_proposal_is_only_diagnostic(self):
        from commentary_modern_reference_gate import (
            validate_pending_source_reference_errata)
        source_target = "Isa.25.8"
        digest = hashlib.sha256(source_target.encode()).hexdigest()
        label_digest = hashlib.sha256(b"Is. 25:8").hexdigest()
        native = {"original_compiled_corpus_sha256": "a" * 64,
                  "chapters": {"Eccl.10": {"original_units": [{
                      "first_key": "Eccl.10.11",
                      "source_unit_sha256": "b" * 64}]}}}
        ledger = {"status":
                  "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
                  "source_reference_labels_or_literal_targets_exported": False,
                  "publication_authorized": False,
                  "pending": [{
                      "source_first_key": "Eccl.10.11",
                      "source_reference_ordinal": 1,
                      "original_osisRef_sha256": digest,
                      "original_visible_label_sha256": label_digest,
                  }]}
        case = {"source_first_key": "Eccl.10.11",
                "original_reference_ordinal": 1,
                "original_native_unit_sha256": "b" * 64,
                "original_target": source_target,
                "original_target_sha256": digest,
                "original_visible_label_sha256": label_digest,
                "finding": "ORIGINAL_DIGITAL_WITNESS_POINTS_TO_WRONG_VERSE",
                "proposed_corrected_target": "Isa.35.8",
                "approval": False}
        manifest = {"status":
                    "PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
                    "original_source": "MHCC 0.1.1 SWORD",
                    "original_native_corpus_sha256": "a" * 64,
                    "original_sword_changed": False,
                    "modern_prose_changed": False,
                    "modern_osis_links_automatically_changed": False,
                    "editorial_target_corrections_approved": False,
                    "redistributed": False, "cases": [case]}
        receipt = validate_pending_source_reference_errata(
            manifest=manifest, ledger=ledger, native=native)
        self.assertEqual(receipt["original_link_occurrences_reconciled"], 1)
        self.assertFalse(receipt["publication_authorized"])
        manifest["cases"][0]["proposed_corrected_target"] = source_target
        with self.assertRaises(ValueError):
            validate_pending_source_reference_errata(
                manifest=manifest, ledger=ledger, native=native)


    def test_private_unplaced_native_note_preview_segregates_prose_and_links(self):
        from copy import deepcopy
        from commentary_modern_reference_gate import (
            build_private_source_reference_supplement)
        ns="http://www.bibletechnologies.net/2003/OSIS/namespace"
        doc=ET.Element(f"{{{ns}}}osis")
        chapter=ET.SubElement(doc,f"{{{ns}}}chapter",{"osisID":"Gen.1"})
        section=ET.SubElement(chapter,f"{{{ns}}}div",{
            "annotateType":"commentary","annotateRef":"Gen.1.1"})
        p=ET.SubElement(section,f"{{{ns}}}p")
        p.text="Modern prose preserves an existing "
        ref=ET.SubElement(p,f"{{{ns}}}reference",{"osisRef":"John.3.16"})
        ref.text="John 3:16"
        ref.tail=" citation."
        base=ET.tostring(doc,encoding="utf-8")
        original={
            "Gen.1.1":[
                ("Bible:Acts.2.1", "2"),
                ("Gen.1.1-Gen.1.4", "1-4"),
                ("Gen.1.1-Gen.2.3", "source heading"),
            ]}
        def row(n):
            literal,label=original["Gen.1.1"][n-1]
            return {
                "source_first_key":"Gen.1.1",
                "source_reference_ordinal":n,
                "original_osisRef_sha256":hashlib.sha256(
                    literal.encode()).hexdigest(),
                "original_visible_label_sha256":hashlib.sha256(
                    label.encode()).hexdigest(),
            }
        ledger={"status":
                "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
                "source_reference_labels_or_literal_targets_exported":False,
                "publication_authorized":False,
                "source_original_links_still_requiring_placement_review":3,
                "pending":[row(1),row(2),row(3)]}
        native={"original_compiled_corpus_sha256":"a"*64,
                "chapters":{"Gen.1":{"original_units":[{
                    "first_key":"Gen.1.1","keys":["Gen.1.1"]}]}}}
        errata={
            "status":"PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
            "original_native_corpus_sha256":"a"*64,
            "original_sword_changed":False,
            "modern_prose_changed":False,
            "modern_osis_links_automatically_changed":False,
            "editorial_target_corrections_approved":False,
            "redistributed":False,
            "cases":[{
                "source_first_key":"Gen.1.1",
                "original_reference_ordinal":3,
                "approval":False,
            }],
        }
        output,receipt=build_private_source_reference_supplement(
            linked_osis=base, ledger=ledger, original=original,
            native=native, errata=errata)
        self.assertEqual(
            receipt["original_link_occurrences_preserved_only_in_separate_source_notes"],2)
        self.assertEqual(receipt["malformed_or_wrong_original_links_excluded_for_review"],1)
        self.assertTrue(receipt["modern_source_text_and_existing_links_unchanged"])
        result=ET.fromstring(output)
        note=result.find(
            f".//{{{ns}}}note[@resp='BibleResourcesPrivateSourceOnlyLinkSupplement']")
        self.assertIsNotNone(note)
        self.assertEqual(
            [x.get("osisRef") for x in note.findall(f"./{{{ns}}}reference")],
            ["Bible:Acts.2.1","Gen.1.1-Gen.1.4"])
        self.assertEqual(
            ["".join(x.itertext()) for x in note.findall(
                f"./{{{ns}}}reference")],
            ["Acts 2:1","Genesis 1:1–4"])
        self.assertNotIn("Gen.1.1-Gen.2.3",output.decode())
        self.assertEqual(len(result.findall(f".//{{{ns}}}reference")),3)
        self.assertEqual(
            "".join(result.find(f".//{{{ns}}}p").itertext()),
            "".join(ET.fromstring(base).find(f".//{{{ns}}}p").itertext()))
        tampered=deepcopy(ledger)
        tampered["pending"][0]["original_visible_label_sha256"]="0"*64
        with self.assertRaises(ValueError):
            build_private_source_reference_supplement(
                linked_osis=base,ledger=tampered,original=original,
                native=native,errata=errata)
        bad=deepcopy(errata)
        bad["editorial_target_corrections_approved"]=True
        with self.assertRaises(ValueError):
            build_private_source_reference_supplement(
                linked_osis=base,ledger=ledger,original=original,
                native=native,errata=bad)


    def test_four_case_errata_navigation_preview_never_mutates_native_links(self):
        from copy import deepcopy
        from commentary_modern_reference_gate import (
            build_unapproved_source_errata_notes_preview)
        ns="http://www.bibletechnologies.net/2003/OSIS/namespace"
        doc=ET.Element(f"{{{ns}}}osis")
        chapter=ET.SubElement(doc,f"{{{ns}}}chapter",{"osisID":"Jer.50"})
        section=ET.SubElement(chapter,f"{{{ns}}}div",{
            "annotateType":"commentary","annotateRef":"Jer.50.1"})
        ET.SubElement(section,f"{{{ns}}}p").text="Original paragraph modernized."
        source_note=ET.SubElement(section,f"{{{ns}}}note",{
            "type":"crossReference",
            "resp":"BibleResourcesPrivateSourceOnlyLinkSupplement"})
        source_note.text="Earlier source-only note."
        base=ET.tostring(doc,encoding="utf-8")
        literal="Jer.50.1-Jer.3.8"
        source_digest=hashlib.sha256(literal.encode()).hexdigest()
        label_digest=hashlib.sha256(b"1-3,8-16").hexdigest()
        ledger={
            "status":
                "SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
            "source_reference_labels_or_literal_targets_exported":False,
            "publication_authorized":False,
            "pending":[{
                "source_first_key":"Jer.50.1",
                "source_reference_ordinal":1,
                "original_osisRef_sha256":source_digest,
                "original_visible_label_sha256":label_digest,
                "full_range_rejection_reason":"CROSS_CHAPTER_RANGE"
            }],
        }
        native={
            "original_compiled_corpus_sha256":"a"*64,
            "chapters":{"Jer.50":{"original_units":[{
                "first_key":"Jer.50.1",
                "keys":["Jer.50.1"],
                "source_unit_sha256":"b"*64
            }]}}
        }
        case={
            "source_first_key":"Jer.50.1",
            "original_reference_ordinal":1,
            "original_native_unit_sha256":"b"*64,
            "original_target":literal,
            "original_target_sha256":source_digest,
            "original_visible_label_sha256":label_digest,
            "finding":"INVALID_CROSS_CHAPTER_NAVIGATION_IN_ORIGINAL_OSISREF",
            "candidate_fragment":"Jer.50.1-Jer.50.3",
            "proposed_navigation_targets_for_unpublished_review":[
                "Jer.50.1-Jer.50.3","Jer.50.8-Jer.50.16"],
            "proposed_navigation_witness_class":"INDEPENDENT_EXPLICIT_OUTLINE",
            "approval":False
        }
        errata={
            "status":"PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
            "original_source":"MHCC 0.1.1 SWORD",
            "original_native_corpus_sha256":"a"*64,
            "original_sword_changed":False,
            "modern_prose_changed":False,
            "modern_osis_links_automatically_changed":False,
            "editorial_target_corrections_approved":False,
            "redistributed":False,
            "cases":[case],
            "proposed_navigation_note_status":
                "UNAPPROVED_SEPARATE_EDITORIAL_REPAIR_PREVIEW_NOT_IN_ORIGINAL_SOURCE",
            "proposed_navigation_note_publication_authorized":False,
            "proposed_navigation_source_links_repaired_in_editorial_preview":1,
            "proposed_navigation_note_count":2
        }
        output,receipt=build_unapproved_source_errata_notes_preview(
            source_note_osis=base,ledger=ledger,native=native,errata=errata)
        self.assertEqual(receipt["original_source_link_occurrences_provisionally_repaired"],1)
        self.assertEqual(receipt["derived_navigation_links_from_corroborating_witnesses"],2)
        self.assertFalse(receipt["editorial_approval"])
        self.assertNotIn(literal,output.decode())
        root=ET.fromstring(output)
        prior=root.find(
            f".//{{{ns}}}note[@resp='BibleResourcesPrivateSourceOnlyLinkSupplement']")
        self.assertEqual(prior.text,source_note.text)
        proposal=root.find(
            f".//{{{ns}}}note[@resp='BibleResourcesPrivateUnapprovedOriginalErrataPreview']")
        self.assertEqual(
            [r.get("osisRef") for r in proposal.findall(f"./{{{ns}}}reference")],
            ["Jer.50.1-Jer.50.3","Jer.50.8-Jer.50.16"])
        self.assertEqual(
            "".join(root.find(f".//{{{ns}}}p").itertext()),
            "Original paragraph modernized.")
        failed=deepcopy(errata)
        failed["cases"][0]["candidate_fragment"]="Jer.51.1-Jer.51.3"
        with self.assertRaises(ValueError):
            build_unapproved_source_errata_notes_preview(
                source_note_osis=base,ledger=ledger,native=native,errata=failed)



def _private_context_relocation_fixture():
    from commentary_modern_draft_osis_preview import NS
    original = (b'<div><p>We recognize how the mighty king shows unusual '
                b'compassion to faithful servants '
                b'<reference osisRef="Bible:John.3.16">John 3:16</reference>'
                b' and sends help.</p></div>')
    contexts = _original_source_link_contexts(original)
    doc = ET.Element(f"{{{NS}}}osis")
    chapter = ET.SubElement(doc,f"{{{NS}}}chapter",{"osisID":"Gen.1"})
    section = ET.SubElement(chapter,f"{{{NS}}}div",{
        "annotateType":"commentary","annotateRef":"Gen.1.1"})
    ET.SubElement(section,f"{{{NS}}}p").text = (
        "The mighty king shows unusual compassion to faithful servants, "
        "even at great personal cost.")
    grouped = ET.SubElement(section,f"{{{NS}}}note",{
        "type":"crossReference",
        "resp":"BibleResourcesPrivateSourceOnlyLinkSupplement"})
    grouped.text="Unplaced links from original edition (not translated citations): "
    target="Bible:John.3.16"
    for ordinal in range(1,177):
        ref=ET.SubElement(grouped,f"{{{NS}}}reference",{"osisRef":target})
        ref.text="John 3:16"
        ref.tail="; " if ordinal <176 else "."
    h=hashlib.sha256(target.encode()).hexdigest()
    pending=[{"source_first_key":"Gen.1.1","source_reference_ordinal":ordinal,
              "original_osisRef_sha256":h,
              "original_visible_label_sha256":"f"*64}
             for ordinal in range(1,181)]
    native={
        "source_prose_or_original_markup_exported":False,
        "original_compiled_corpus_sha256":FULL_HASH,
        "chapters":{"Gen.1":{"original_units":[
            {"first_key":"Gen.1.1","keys":["Gen.1.1"]}]}}}
    errata={"status":"PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
            "original_native_corpus_sha256":FULL_HASH,
            "cases":[{"source_first_key":"Gen.1.1",
                      "original_reference_ordinal":n,"approval":False}
                     for n in range(177,181)]}
    ledger={
        "status":"SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
        "source_reference_labels_or_literal_targets_exported":False,
        "publication_authorized":False,
        "source_original_links_still_requiring_placement_review":180,
        "pending":pending,
    }
    by_ordinal=[contexts[0]]+ [("", "")]*179
    return ET.tostring(doc), ledger, native, errata, {"Gen.1.1":by_ordinal}


class PrivateOriginalContextRelocationTests(unittest.TestCase):
    def test_original_context_is_extracted_without_changing_the_source(self):
        raw=(b'<div>Some substantial leading exposition before '
             b'<reference osisRef="Bible:John.3.16">Jn 3:16</reference>'
             b' and then the original conclusion.</div>')
        contexts=_original_source_link_contexts(raw)
        self.assertEqual(len(contexts),1)
        self.assertTrue(contexts[0][0].endswith("before "))
        self.assertTrue(contexts[0][1].startswith(" and then"))

    def test_unique_context_moves_one_link_without_losing_the_other_175(self):
        from commentary_modern_draft_osis_preview import NS
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        output,report=build_private_contextual_source_note_preview(
            source_note_osis=source,ledger=ledger,native=native,
            errata=errata,original_contexts=contexts)
        root=ET.fromstring(output)
        self.assertEqual(report["source_notes_moved_to_authored_paragraphs"],1)
        self.assertEqual(report["source_notes_still_grouped_by_K"],175)
        notes=[x for x in root.iter() if x.tag==f"{{{NS}}}note"]
        self.assertEqual(len(notes),2)
        local=[n for n in notes if n.get("resp")==
               "BibleResourcesPrivateContextSourceLink"]
        self.assertEqual(len(local),1)
        self.assertIn("context matches",local[0].text)
        self.assertEqual(local[0][0].get("osisRef"),"Bible:John.3.16")
        links=[x for n in notes for x in n if x.tag==f"{{{NS}}}reference"]
        self.assertEqual(len(links),176)
        self.assertIn("faithful servants", "".join(root.itertext()))

    def test_repeated_generic_or_ambiguous_context_remains_unplaced(self):
        from commentary_modern_draft_osis_preview import NS
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        root=ET.fromstring(source)
        p=next(n for n in root.iter() if n.tag==f"{{{NS}}}p")
        p.text=p.text+" Again, the mighty king shows unusual compassion to faithful servants."
        self.assertIsNone(_source_context_unique_paragraph_anchor(
            next(n for n in root.iter() if n.get("annotateRef")=="Gen.1.1"),
            contexts["Gen.1.1"][0]))
        output,report=build_private_contextual_source_note_preview(
            source_note_osis=ET.tostring(root),ledger=ledger,native=native,
            errata=errata,original_contexts=contexts)
        self.assertEqual(report["source_notes_moved_to_authored_paragraphs"],0)
        self.assertEqual(report["source_notes_still_grouped_by_K"],176)

    def test_rewritten_original_link_target_fails_closed(self):
        from commentary_modern_draft_osis_preview import NS
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        root=ET.fromstring(source)
        link=next(n for n in root.iter() if n.tag==f"{{{NS}}}reference")
        link.set("osisRef","Bible:John.3.17")
        with self.assertRaisesRegex(ValueError,"authenticated source target"):
            build_private_contextual_source_note_preview(
                source_note_osis=ET.tostring(root),ledger=ledger,native=native,
                errata=errata,original_contexts=contexts)



    def test_modernized_sentence_can_only_get_paragraph_local_provenance(self):
        from commentary_modern_draft_osis_preview import NS
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        root=ET.fromstring(source)
        paragraph=next(n for n in root.iter() if n.tag==f"{{{NS}}}p")
        paragraph.text=(
            "The covenant promises redemption and mercy to scattered families "
            "through endurance, humble service and lasting hope.")
        contexts["Gen.1.1"][0]=(
            "The ancient covenant promised redemption and mercy for scattered "
            "families through patient endurance, humble service, and steadfast hope.",
            " Other unrelated original exposition follows.")
        section=next(n for n in root.iter() if n.get("annotateRef")=="Gen.1.1")
        place=_source_context_unique_paragraph_anchor(section,contexts["Gen.1.1"][0])
        self.assertIsNotNone(place)
        self.assertIs(place[0],paragraph)
        self.assertEqual(place[1],-1)
        _,report=build_private_contextual_source_note_preview(
            source_note_osis=ET.tostring(root),ledger=ledger,native=native,
            errata=errata,original_contexts=contexts)
        self.assertEqual(report["source_notes_moved_to_authored_paragraphs"],1)
        self.assertEqual(report["paragraph_lexical_context_proximity_count"],1)
        self.assertEqual(report["exact_phrase_proximity_count"],0)

    def test_shared_semantic_vocab_in_two_paragraphs_is_not_enough(self):
        from commentary_modern_draft_osis_preview import NS
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        root=ET.fromstring(source)
        section=next(n for n in root.iter() if n.get("annotateRef")=="Gen.1.1")
        first=next(n for n in section if n.tag==f"{{{NS}}}p")
        first.text=("The covenant promises redemption and mercy to scattered "
                    "families through endurance, humble service and lasting hope.")
        second=ET.Element(f"{{{NS}}}p")
        second.text=("The same covenant promises redemption and mercy to "
                     "scattered families through endurance, humble service and hope.")
        section.insert(1,second)
        context=("The ancient covenant promised redemption and mercy for scattered "
                 "families through patient endurance, humble service, and steadfast hope.",
                 " Other unrelated original exposition follows.")
        self.assertIsNone(_source_context_unique_paragraph_anchor(section,context))


    def test_original_full_k_order_brackets_a_modern_sentence(self):
        from commentary_modern_draft_osis_preview import NS
        section=ET.Element(f"{{{NS}}}div")
        p=ET.SubElement(section,f"{{{NS}}}p")
        p.text=("The entire congregation gathered together beside the mountain "
                "and listened with careful attention. Then the servant returned "
                "with unexpected gifts and a message of peace.")
        raw=(b"<div>The entire congregation gathered together beside the mountain "
             b"and listened with careful attention "
             b'<reference osisRef="Bible:Ps.4.2">Psalm 4:2</reference>'
             b". Then the servant returned with unexpected gifts "
             b"and a message of peace.</div>")
        result=_source_owned_ordered_alignment(raw,section)
        self.assertEqual(len(result["original_link_offsets"]),1)
        self.assertIn(1,result["suggestions"])
        para,offset=result["suggestions"][1]
        self.assertIs(para,p)
        self.assertEqual(p.text[:offset][-10:],"attention.")

    def test_full_k_order_without_two_sided_distinctive_anchors_is_unplaced(self):
        from commentary_modern_draft_osis_preview import NS
        section=ET.Element(f"{{{NS}}}div")
        ET.SubElement(section,f"{{{NS}}}p").text=(
            "A person is kind and should listen. Everyone remembers grace.")
        raw=(b'<div>Some other words unrelated to the modern statement '
             b'<reference osisRef="Bible:Gen.1.2">Genesis 1:2</reference>'
             b'and unlike everything following it.</div>')
        result=_source_owned_ordered_alignment(raw,section)
        self.assertEqual(result["suggestions"],{})



    def test_all_176_original_references_visible_without_claiming_inline_words(self):
        from commentary_modern_draft_osis_preview import NS
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        target="Bible:John.3.16"
        hash_target=hashlib.sha256(target.encode()).hexdigest()
        hash_display=hashlib.sha256(b"John 3:16").hexdigest()
        receipt={
            "status":"PRIVATE_NATIVE_SOURCE_NOTE_ALTERNATIVE_NOT_AUTHORED_INLINE_PARITY",
            "original_link_occurrences_preserved_only_in_separate_source_notes":176,
            "source_link_supplement_not_authorial_or_inline":True,
            "published_or_distributed":False,
            "original_native_corpus_sha256":FULL_HASH,
            "source_first_K_sections_with_note":1,
            "note_source_K_reference_hashes_for_private_native_readback":[{
                "source_first_key":"Gen.1.1",
                "original_source_reference_hashes":[{
                    "source_original_literal_target_sha256":hash_target,
                    "supplement_display_sha256":hash_display,
                } for _ in range(176)]
            }]
        }
        output,report=build_private_inline_original_reference_index(
            source_note_osis=source,source_receipt=receipt,native=native)
        root=ET.fromstring(output)
        self.assertEqual(report["original_unplaced_valid_references_visible_in_commentary"],176)
        self.assertEqual(report["original_K_groups_with_reference_index"],1)
        self.assertFalse(report["precise_original_sentence_locations_proven"])
        self.assertFalse(report["published_or_distributed"])
        self.assertEqual(len([x for x in root.iter()
            if x.tag==f"{{{NS}}}reference"]),176)
        self.assertEqual(len([x for x in root.iter()
            if x.tag==f"{{{NS}}}note"]),0)
        ref_p=[x for x in root.iter() if x.tag==f"{{{NS}}}p" and
               x.get("resp")=="BibleResourcesOriginalSourceReferenceIndexOnly"]
        self.assertEqual(len(ref_p),1)
        self.assertEqual(len(ref_p[0]),176)
        self.assertIn("exact original sentence locations unverified",ref_p[0].text)
        self.assertIn("faithful servants", "".join(root.itertext()))

    def test_visible_reference_index_rejects_wrong_source_sha(self):
        source,ledger,native,errata,contexts=_private_context_relocation_fixture()
        with self.assertRaisesRegex(ValueError,"Cannot promote unsourced"):
            build_private_inline_original_reference_index(
                source_note_osis=source,source_receipt={
                    "status":"PRIVATE_NATIVE_SOURCE_NOTE_ALTERNATIVE_NOT_AUTHORED_INLINE_PARITY",
                    "original_link_occurrences_preserved_only_in_separate_source_notes":176,
                    "source_link_supplement_not_authorial_or_inline":True,
                    "published_or_distributed":False,
                    "original_native_corpus_sha256":"0"*64
                },native=native)



class PrivateCompactOriginalCrossReferenceTests(unittest.TestCase):
    def fixture(self, repeat=False):
        from commentary_modern_draft_osis_preview import NS
        root=ET.Element(f"{{{NS}}}osis")
        chapter=ET.SubElement(root,f"{{{NS}}}chapter",{"osisID":"1Cor.13"})
        sec=ET.SubElement(chapter,f"{{{NS}}}div",{
            "annotateType":"commentary","annotateRef":"1Cor.13.8"})
        p=ET.SubElement(sec,f"{{{NS}}}p")
        p.text="God is love (1 John 4:8, 16). He is faithful."
        if repeat:
            ET.SubElement(sec,f"{{{NS}}}p").text=(
                "God is love (1 John 4:8, 16).")
        old=[("1John.4.8","1Jo 4:8"),("1John.4.16","16")]
        old.extend([("Matt.23.1","x")]*4)
        pending=[{
            "source_first_key":"1Cor.13.8",
            "source_reference_ordinal":i,
            "original_osisRef_sha256":hashlib.sha256(t.encode()).hexdigest(),
            "original_visible_label_sha256":hashlib.sha256(l.encode()).hexdigest(),
            "disposition":"UNPLACED_SINGLE_VERSE_REFERENCE"
        } for i,(t,l) in enumerate(old,1)]
        native={
            "source_prose_or_original_markup_exported":False,
            "original_compiled_corpus_sha256":FULL_HASH,
            "chapters":{"1Cor.13":{"original_units":[{
                "first_key":"1Cor.13.8","keys":["1Cor.13.8"]}]}}
        }
        ledger={
            "status":"SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
            "source_reference_labels_or_literal_targets_exported":False,
            "publication_authorized":False,
            "original_native_reference_elements":6,
            "source_spurious_link_occurrences_explicitly_omitted":0,
            "source_link_occurrences_verified_in_derived_osis":0,
            "source_original_links_still_requiring_placement_review":6,
            "pending":pending,
        }
        errata={
            "status":"PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
            "original_native_corpus_sha256":FULL_HASH,
            "cases":[{"source_first_key":"1Cor.13.8",
                      "original_reference_ordinal":i,"approval":False}
                     for i in range(3,7)]}
        return ET.tostring(root),ledger,{"1Cor.13.8":old},native,errata

    def test_two_separate_real_verse_targets_in_one_compact_english_citation(self):
        from commentary_modern_draft_osis_preview import NS
        root,ledger,old,native,errata=self.fixture()
        result,revised,receipt=build_private_compact_original_crossrefs(
            linked_osis=root,ledger=ledger,original=old,native=native,errata=errata)
        doc=ET.fromstring(result)
        refs=[n for n in doc.iter() if n.tag==f"{{{NS}}}reference"]
        self.assertEqual(len(refs),2)
        self.assertEqual([(r.text,r.get("osisRef")) for r in refs],
                         [("8","1John.4.8"),("16","1John.4.16")])
        self.assertEqual("".join(doc.itertext()),
                         "God is love (1 John 4:8, 16). He is faithful.")
        self.assertEqual(receipt["original_exact_compact_verse_links_restored"],2)
        self.assertEqual(receipt["original_defective_link_proposals_never_retargeted"],4)
        self.assertEqual(len(revised["pending"]),4)
        self.assertFalse(receipt["released_or_distributed"])

    def test_duplicate_english_citation_in_same_K_remains_unplaced(self):
        root,ledger,old,native,errata=self.fixture(repeat=True)
        _,revised,receipt=build_private_compact_original_crossrefs(
            linked_osis=root,ledger=ledger,original=old,native=native,errata=errata)
        self.assertEqual(receipt["original_exact_compact_verse_links_restored"],0)
        self.assertEqual(len(revised["pending"]),6)

    def test_wrong_original_sha_blocks_recovery(self):
        root,ledger,old,native,errata=self.fixture()
        ledger["pending"][0]["original_osisRef_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Original exact source link receipt changed"):
            build_private_compact_original_crossrefs(
                linked_osis=root,ledger=ledger,original=old,native=native,
                errata=errata)


    def test_inherited_book_in_parenthetical_citation_crosses_existing_link(self):
        from commentary_modern_draft_osis_preview import NS
        raw,ledger,original,native,errata=self.fixture()
        root=ET.fromstring(raw)
        p=next(x for x in root.iter() if x.tag==f"{{{NS}}}p")
        p.text="Jeremiah 32:"
        present=ET.SubElement(p,f"{{{NS}}}reference",{"osisRef":"Jer.32.5"})
        present.text="5"
        present.tail="; 34:3."
        original["1Cor.13.8"][0]=("Jer.34.3","34:3")
        target,label=original["1Cor.13.8"][0]
        ledger["pending"][0]["original_osisRef_sha256"]=hashlib.sha256(target.encode()).hexdigest()
        ledger["pending"][0]["original_visible_label_sha256"]=hashlib.sha256(label.encode()).hexdigest()
        output,_,receipt=build_private_compact_original_crossrefs(
            linked_osis=ET.tostring(root),ledger=ledger,
            original=original,native=native,errata=errata)
        new=ET.fromstring(output)
        links=[x for x in new.iter() if x.tag==f"{{{NS}}}reference"]
        self.assertEqual([(x.text,x.get("osisRef")) for x in links],
                         [("5","Jer.32.5"),("3","Jer.34.3")])
        self.assertEqual("".join(new.itertext()),"Jeremiah 32:5; 34:3.")
        self.assertEqual(receipt["original_exact_compact_verse_links_restored"],1)

    def test_single_chapter_citation_jude_15_is_unambiguous(self):
        from commentary_modern_draft_osis_preview import NS
        raw,ledger,original,native,errata=self.fixture()
        root=ET.fromstring(raw)
        p=next(x for x in root.iter() if x.tag==f"{{{NS}}}p")
        p.text="God will judge every cruel word (Jude 15)."
        original["1Cor.13.8"][0]=("Jude.1.15","Jude 1:15")
        target,label=original["1Cor.13.8"][0]
        ledger["pending"][0]["original_osisRef_sha256"]=hashlib.sha256(target.encode()).hexdigest()
        ledger["pending"][0]["original_visible_label_sha256"]=hashlib.sha256(label.encode()).hexdigest()
        output,_,receipt=build_private_compact_original_crossrefs(
            linked_osis=ET.tostring(root),ledger=ledger,
            original=original,native=native,errata=errata)
        new=ET.fromstring(output)
        links=[x for x in new.iter() if x.tag==f"{{{NS}}}reference"]
        self.assertEqual([(x.text,x.get("osisRef")) for x in links],
                         [("15","Jude.1.15")])
        self.assertEqual("".join(new.itertext()),
                         "God will judge every cruel word (Jude 15).")
        self.assertEqual(receipt["original_exact_compact_verse_links_restored"],1)


class OriginalKTargetRangeHeadingLinksTests(unittest.TestCase):
    @staticmethod
    def fixture(range_literal="Gen.8.13-Gen.8.19",
                printed_label="Gen 8:13-19",
                next_title="The waters recede (verses 13–19)"):
        from commentary_modern_draft_osis_preview import NS, _range
        doc=ET.Element(f"{{{NS}}}osis")
        ch=ET.SubElement(doc,f"{{{NS}}}chapter",{"osisID":"Gen.8"})
        groups=[
            {"first_key":"Gen.8.4",
             "keys":[f"Gen.8.{x}" for x in range(4,13)]},
            {"first_key":"Gen.8.13",
             "keys":[f"Gen.8.{x}" for x in range(13,20)]},
        ]
        first=ET.SubElement(ch,f"{{{NS}}}div",{
            "annotateType":"commentary","annotateRef":_range(groups[0]["keys"])})
        ET.SubElement(first,f"{{{NS}}}title",{"type":"sub"}).text=(
            "The waters slowly retreat (verses 4–12)")
        ET.SubElement(first,f"{{{NS}}}p").text="The Lord preserved Noah's family."
        following=ET.SubElement(ch,f"{{{NS}}}div",{
            "annotateType":"commentary","annotateRef":_range(groups[1]["keys"])})
        ET.SubElement(following,f"{{{NS}}}title",{"type":"sub"}).text=next_title
        ET.SubElement(following,f"{{{NS}}}p").text="The earth became dry."
        originals=[(range_literal,printed_label)]
        originals.extend([("John.3.16","not applicable")]*4)
        pending=[{
            "source_first_key":"Gen.8.4","source_reference_ordinal":i,
            "original_osisRef_sha256":hashlib.sha256(t.encode()).hexdigest(),
            "original_visible_label_sha256":hashlib.sha256(l.encode()).hexdigest(),
        } for i,(t,l) in enumerate(originals,1)]
        ledger={
            "status":"SOURCE_NATIVE_WHOLE_CANON_HYPERLINK_DISPOSITION_QUEUE_NOT_FINAL_APPROVAL",
            "original_native_reference_elements":5,
            "source_link_occurrences_verified_in_derived_osis":0,
            "source_spurious_link_occurrences_explicitly_omitted":0,
            "source_original_links_still_requiring_placement_review":5,
            "source_reference_labels_or_literal_targets_exported":False,
            "publication_authorized":False,"pending":pending}
        native={"source_prose_or_original_markup_exported":False,
                "original_compiled_corpus_sha256":FULL_HASH,
                "chapters":{"Gen.8":{"original_units":groups}}}
        errata={"status":"PINNED_ORIGINAL_LINK_ERRATA_REVIEW_ONLY_NOT_APPLIED",
                "original_native_corpus_sha256":FULL_HASH,
                "cases":[{"source_first_key":"Gen.8.4",
                          "original_reference_ordinal":i,"approval":False}
                         for i in range(2,6)]}
        return ET.tostring(doc),ledger,{"Gen.8.4":originals},native,errata

    def test_source_trailing_link_becomes_exact_next_K_heading_navigation(self):
        from commentary_modern_draft_osis_preview import NS
        args=self.fixture()
        output,ledger,receipt=build_private_owned_K_heading_range_links(
            compact_osis=args[0],ledger=args[1],original=args[2],
            native=args[3],errata=args[4])
        root=ET.fromstring(output)
        matches=[x for x in root.iter()
                 if x.tag==f"{{{NS}}}reference"]
        self.assertEqual(len(matches),1)
        self.assertEqual(matches[0].get("osisRef"),"Gen.8.13-Gen.8.19")
        self.assertEqual(matches[0].text,"verses 13–19")
        self.assertEqual(receipt["source_original_links_restored_to_matching_modern_K_headings"],1)
        self.assertEqual(receipt["source_valid_references_still_in_section_notes"],0)
        self.assertEqual(len(ledger["pending"]),4)
        self.assertEqual("".join(root.itertext()),
                         "The waters slowly retreat (verses 4–12)"
                         "The Lord preserved Noah's family."
                         "The waters recede (verses 13–19)"
                         "The earth became dry.")

    def test_partial_target_original_K_or_nonmatching_heading_is_not_linked(self):
        for literal,heading in [
            ("Gen.8.13-Gen.8.18","The waters recede (verses 13–18)"),
            ("Gen.8.13-Gen.8.19","The waters recede (verses 13–18)"),
        ]:
            with self.subTest(literal=literal,heading=heading):
                args=self.fixture(range_literal=literal,
                    printed_label=("Gen 8:13-18" if literal.endswith(".18")
                                   else "Gen 8:13-19"),next_title=heading)
                output,ledger,receipt=build_private_owned_K_heading_range_links(
                    compact_osis=args[0],ledger=args[1],original=args[2],
                    native=args[3],errata=args[4])
                self.assertEqual(receipt["source_original_links_restored_to_matching_modern_K_headings"],0)
                self.assertEqual(receipt["source_valid_references_still_in_section_notes"],1)
                self.assertEqual(len(ledger["pending"]),5)

    def test_original_source_link_identity_mismatch_fails_closed(self):
        args=self.fixture()
        args[1]["pending"][0]["original_osisRef_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"Unpinned original link"):
            build_private_owned_K_heading_range_links(
                compact_osis=args[0],ledger=args[1],original=args[2],
                native=args[3],errata=args[4])

    def test_source_printed_verse_span_must_agree_with_target(self):
        args=self.fixture(printed_label="Gen 8:13-18")
        _,ledger,receipt=build_private_owned_K_heading_range_links(
            compact_osis=args[0],ledger=args[1],original=args[2],
            native=args[3],errata=args[4])
        self.assertEqual(receipt["source_original_links_restored_to_matching_modern_K_headings"],0)
        self.assertEqual(len(ledger["pending"]),5)


    def test_explicit_partial_verse_span_inside_its_authenticated_original_K(self):
        from commentary_modern_draft_osis_preview import NS
        raw,ledger,original,native,errata=self.fixture(
            range_literal="Gen.8.7-Gen.8.9",printed_label="Gen 8:7-9")
        doc=ET.fromstring(raw)
        section=next(x for x in doc.iter()
                     if x.get("annotateRef")=="Gen.8.4-Gen.8.12")
        p=section.find(f"./{{{NS}}}p")
        p.text="Noah followed God's plan. Verses 7–9 describe the birds."
        before="".join(doc.itertext())
        out,remaining,receipt=build_private_owned_K_heading_range_links(
            compact_osis=ET.tostring(doc),ledger=ledger,original=original,
            native=native,errata=errata)
        fixed=ET.fromstring(out)
        references=[x for x in fixed.iter() if x.tag==f"{{{NS}}}reference"]
        self.assertEqual(len(references),1)
        self.assertEqual(references[0].get("osisRef"),"Gen.8.7-Gen.8.9")
        self.assertEqual(references[0].text,"Verses 7–9")
        self.assertEqual(receipt["source_original_links_restored_to_matching_modern_K_headings"],0)
        self.assertEqual(receipt["source_original_partial_ranges_restored_in_K_exposition"],1)
        self.assertEqual(len(remaining["pending"]),4)
        self.assertEqual("".join(fixed.itertext()),before)

    def test_original_single_first_verse_K_preserves_authored_later_chapter_range(self):
        from commentary_modern_draft_osis_preview import NS, _range
        raw,ledger,original,native,errata=self.fixture(
            range_literal="Isa.12.4-Isa.12.6",printed_label="Is. 12:4-6")
        doc=ET.fromstring(raw)
        chapter=next(x for x in doc.iter() if x.tag==f"{{{NS}}}chapter")
        chapter.set("osisID","Isa.12")
        secs=chapter.findall(f"./{{{NS}}}div[@annotateType='commentary']")
        chapter.remove(secs[1])
        secs[0].set("annotateRef","Isa.12.1")
        secs[0].find(f"./{{{NS}}}p").text=(
            "In the latter part of the song (verses 4–6), believers urge "
            "each other to praise the Lord.")
        old=original.pop("Gen.8.4")
        original["Isa.12.1"]=old
        for row in ledger["pending"]:
            row["source_first_key"]="Isa.12.1"
        native["chapters"]={"Isa.12":{"original_units":[{
            "first_key":"Isa.12.1","keys":["Isa.12.1"]}]}}
        for case in errata["cases"]:
            case["source_first_key"]="Isa.12.1"
        before="".join(doc.itertext())
        out,remaining,receipt=build_private_owned_K_heading_range_links(
            compact_osis=ET.tostring(doc),ledger=ledger,
            original=original,native=native,errata=errata)
        fixed=ET.fromstring(out)
        references=[x for x in fixed.iter() if x.tag==f"{{{NS}}}reference"]
        self.assertEqual(len(references),1)
        self.assertEqual(references[0].get("osisRef"),"Isa.12.4-Isa.12.6")
        self.assertEqual(references[0].text,"verses 4–6")
        self.assertEqual(receipt["source_original_partial_ranges_restored_in_K_exposition"],1)
        self.assertEqual("".join(fixed.itertext()),before)

if __name__=="__main__":
    unittest.main()
