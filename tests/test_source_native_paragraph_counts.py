"""Source p versus typed compiled x-p milestone count, never Bible words."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_native_paragraph_counts import compare_authored_native_paragraphs, ParagraphAuditError

MAPPING=[("GEN","Gen"),("EXO","Exod")]


class TypedParagraphBookTests(unittest.TestCase):
    def test_identifies_per_book_one_paragraph_differences_without_edition_exceptions(self):
        source=(b'<usfx>'
                b'<book id="GEN"><c id="1"/>'
                b'<p><v id="1"/>PRIVATE SOURCE A</p>'
                b'<p><v id="2"/>PRIVATE SOURCE B</p></book>'
                b'<book id="EXO"><c id="1"/>'
                b'<p><v id="1"/>PRIVATE SOURCE C</p>'
                b'<p><v id="2"/>PRIVATE SOURCE D</p>'
                b'</book></usfx>')
        result=compare_authored_native_paragraphs(source,MAPPING,
                                                   {"Gen":1,"Exod":1})
        self.assertEqual(result["source_original_book_count"],2)
        self.assertEqual(result["authorial_native_typed_paragraph_totals"][
            "authorial_p_events"],4)
        self.assertEqual(result["authorial_native_typed_paragraph_totals"][
            "native_typed_x_p_pairs"],2)
        self.assertEqual(result["authorial_native_typed_paragraph_totals"][
            "books_with_p_pair_count_mismatch"],2)
        self.assertTrue(result["every_original_book_has_one_extra_p_vs_compiled"])
        self.assertEqual(result["original_p_position_class_counts"][
            "original_p_before_first_book_verse"],2)
        self.assertFalse(result["source_to_compiled_exact_paragraph_position_equivalence_verified"])
        self.assertFalse(result["publication_approved"])
        self.assertNotIn("PRIVATE",str(result))
        self.assertNotIn("SOURCE",str(result))

    def test_exact_count_is_not_exact_position_fidelity(self):
        source=(b'<usfx><book id="GEN"><c id="1"/>'
                b'<p><v id="1"/>A</p><p><v id="2"/>B</p></book></usfx>')
        result=compare_authored_native_paragraphs(source,[("GEN","Gen")],
                                                   {"Gen":2})
        self.assertEqual(result["authorial_native_typed_paragraph_totals"][
            "books_with_exact_p_pair_count"],1)
        self.assertEqual(result["authorial_native_typed_paragraph_totals"][
            "books_with_p_pair_count_mismatch"],0)
        self.assertFalse(result["source_to_compiled_exact_paragraph_position_equivalence_verified"])

    def test_paragraph_inside_note_remains_visible_not_counted_as_main_text(self):
        source=(b'<usfx><book id="GEN"><c id="1"/>'
                b'<v id="1"/>A<f><p>PRIVATE NOTE</p></f></book></usfx>')
        result=compare_authored_native_paragraphs(source,[("GEN","Gen")],{})
        self.assertEqual(result["original_p_position_class_counts"][
            "original_p_nested_in_note"],1)
        self.assertEqual(result["authorial_native_typed_paragraph_totals"][
            "authorial_p_events"],1)
        self.assertFalse(result["source_to_compiled_exact_paragraph_position_equivalence_verified"])
        self.assertNotIn("PRIVATE",str(result))

    def test_source_books_or_crosswalk_must_not_be_silently_dropped(self):
        source=(b'<usfx><book id="GEN"><c id="1"/><p><v id="1"/>A</p>'
                b'</book></usfx>')
        with self.assertRaises(ParagraphAuditError):
            compare_authored_native_paragraphs(source,[("GEN","Gen"),("EXO","Exod")],
                                               {"Gen":1})
        with self.assertRaises(ParagraphAuditError):
            compare_authored_native_paragraphs(source,[("GEN","Gen")],
                                               {"Other":1})
        with self.assertRaises(ParagraphAuditError):
            compare_authored_native_paragraphs(source,[("GEN","Gen"),("GEN","Exod")],
                                               {"Gen":1})

    def test_unmapped_extra_authorial_book_is_reported_not_silently_dropped(self):
        raw=(b'<usfx><book id="GEN"><c id="1"/>'
             b'<p><v id="1"/>PRIVATE MAPPED</p></book>'
             b'<book id="GLO"><c id="1"/>'
             b'<p><v id="1"/>PRIVATE EXTRA</p></book></usfx>')
        result=compare_authored_native_paragraphs(raw,[("GEN","Gen")],
                                                   {"Gen":1})
        self.assertEqual(result["source_original_book_count"],2)
        self.assertEqual(result["source_mapped_book_count"],1)
        totals=result["authorial_native_typed_paragraph_totals"]
        self.assertEqual(totals["unmapped_source_book_count"],1)
        self.assertEqual(totals["unmapped_source_p_element_count"],1)
        self.assertTrue(result["unmapped_original_book_scope_requires_separate_review"])
        self.assertFalse(result["source_to_compiled_exact_paragraph_position_equivalence_verified"])
        self.assertFalse(result["every_original_book_has_one_extra_p_vs_compiled"])
        self.assertNotIn("PRIVATE",str(result))

    def test_source_extra_paragraph_at_book_intro_is_tracked(self):
        source=(b'<usfx><book id="GEN"><p>PRIVATE INTRO</p>'
                b'<c id="1"/><p><v id="1"/>A</p></book></usfx>')
        result=compare_authored_native_paragraphs(source,[("GEN","Gen")],
                                                   {"Gen":1})
        self.assertEqual(result["original_p_position_class_counts"][
            "original_p_before_first_chapter"],1)
        self.assertEqual(result["original_p_position_class_counts"][
            "original_p_before_first_book_verse"],2)
        self.assertEqual(result["first_per_book_mismatches_no_text"][0][
            "signed_difference"],1)



    def test_prefatory_p_textful_empty_and_notes_are_distinguished_without_leaks(self):
        from source_native_paragraph_counts import audit_usfx_book_prefaces
        xml=(b'<usfx><book id="GEN"><p>PRIVATE INTRODUCTION</p><c id="1"/>'
             b'<p><v id="1"/>VERSE</p></book>'
             b'<book id="EXO"><p sfm="p"><f>PRIVATE NOTE</f></p>'
             b'<c id="1"/><p><v id="1"/>VERSE</p></book></usfx>')
        receipt=audit_usfx_book_prefaces(xml,MAPPING)
        counts=receipt["prefatory_source_p_class_counts"]
        self.assertEqual(counts["mapped_original_books"],2)
        self.assertEqual(counts["prefatory_p_elements"],2)
        self.assertEqual(counts["prefatory_p_with_any_descendant_text"],2)
        self.assertEqual(counts["prefatory_p_with_non_annotation_text"],1)
        self.assertEqual(counts["prefatory_p_without_non_annotation_text"],1)
        self.assertEqual(counts["prefatory_p_with_attributes"],1)
        self.assertFalse(receipt["compiled_book_intro_structure_verified"])
        self.assertFalse(receipt["publication_approved"])
        self.assertNotIn("PRIVATE",str(receipt))

    def test_empty_prefatory_p_and_missing_book_are_visible(self):
        from source_native_paragraph_counts import audit_usfx_book_prefaces
        xml=(b'<usfx><book id="GEN"><p/><c id="1"/><v id="1"/>A</book>'
             b'<book id="EXO"><c id="1"/><v id="1"/>B</book></usfx>')
        r=audit_usfx_book_prefaces(xml,MAPPING)
        c=r["prefatory_source_p_class_counts"]
        self.assertEqual(c["prefatory_p_without_descendant_text"],1)
        self.assertEqual(c["books_without_exactly_one_prefatory_p"],1)
        with self.assertRaises(ParagraphAuditError):
            audit_usfx_book_prefaces(xml,[("GEN","Gen"),("LEV","Lev")])

    def test_source_preface_explicit_title_style_never_conflated_with_plain_p(self):
        from source_native_paragraph_counts import audit_usfx_book_prefaces
        xml=(b'<usfx>'
             b'<book id="GEN"><p sfm="mt1">PRIVATE BOOK TITLE</p>'
             b'<c id="1"/><v id="1"/>VERSE</book>'
             b'<book id="EXO"><p>PRIVATE BODY INTRO</p>'
             b'<c id="1"/><v id="1"/>VERSE</book>'
             b'</usfx>')
        result=audit_usfx_book_prefaces(xml,MAPPING)
        counts=result["prefatory_p_sfm_style_counts"]
        self.assertEqual(counts["family_book_title_style"],1)
        self.assertEqual(counts["family_implicit_p"],1)
        self.assertEqual(counts["sfm_mt1"],1)
        self.assertEqual(counts["sfm_implicit_p"],1)
        self.assertFalse(result["all_prefatory_p_have_allowlisted_book_title_sfm"])
        self.assertFalse(result["source_sfm_to_native_title_semantics_verified"])
        self.assertTrue(result["unknown_sfm_values_are_not_exposed"])
        self.assertNotIn("PRIVATE",str(result))

    def test_unknown_sfm_and_private_css_values_are_never_disclosed(self):
        from source_native_paragraph_counts import audit_usfx_book_prefaces
        xml=(b'<usfx><book id="GEN">'
             b'<p sfm="PRIVATE_UNKNOWN_SFM" style="PRIVATE_CSS_CLASS" level="3">'
             b'PRIVATE ORIGINAL TITLE</p><c id="1"/><v id="1"/>VERSE'
             b'</book></usfx>')
        receipt=audit_usfx_book_prefaces(xml,[("GEN","Gen")])
        c=receipt["prefatory_p_sfm_style_counts"]
        self.assertEqual(c["family_unreviewed_sfm_value"],1)
        self.assertEqual(c["sfm_other_unreviewed_style"],1)
        self.assertEqual(c["with_separate_style_attribute"],1)
        self.assertEqual(c["sfm_and_style_differ"],1)
        self.assertEqual(c["with_level_attribute"],1)
        self.assertFalse(receipt["all_prefatory_p_have_allowlisted_book_title_sfm"])
        self.assertEqual(receipt["first_prefatory_p_sfm_styles_no_text"][0][
            "allowlisted_sfm_code"],"other_unreviewed_style")
        for value in ("PRIVATE_UNKNOWN_SFM","PRIVATE_CSS_CLASS","PRIVATE ORIGINAL TITLE"):
            self.assertNotIn(value,str(receipt))

    def test_known_style_codes_and_unreviewed_values_classify_conservatively(self):
        from source_native_paragraph_counts import classify_prefatory_p_sfm
        self.assertEqual(classify_prefatory_p_sfm("mt"),("book_title_style","mt"))
        self.assertEqual(classify_prefatory_p_sfm("imt2"),("book_title_style","imt2"))
        self.assertEqual(classify_prefatory_p_sfm("s1"),("section_heading_style","s1"))
        self.assertEqual(classify_prefatory_p_sfm("p"),("body_paragraph_style","p"))
        self.assertEqual(classify_prefatory_p_sfm("sp"),("body_paragraph_style","sp"))
        self.assertEqual(classify_prefatory_p_sfm(None),("implicit_p","implicit_p"))
        self.assertEqual(classify_prefatory_p_sfm("A_NEW_STYLE"),
                         ("unreviewed_sfm_value","other_unreviewed_style"))

if __name__=="__main__":
    unittest.main()
