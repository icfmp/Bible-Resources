"""Regression tests for reversible text-only parallel OSIS heading markup."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from osis_text_only_parallels import (
    OSIS,UNLINKED_SEG_TYPE,convert_unresolved_parallel_headings)
from pilot_preflight import PilotError


class ParallelHeadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src=Path(self.tmp.name)/"authoring-conversion.osis.xml"
        self.dest=Path(self.tmp.name)/"preview.osis.xml"
        self.original='''<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
 <osisText>
  <div type="book" osisID="John">
   <chapter sID="John.3"/>
   <title>Actual section heading</title>
   <title type="parallel">V. 22-36: cf.
    <reference type="parallel">Jn 1:6-12, 19-34.</reference>
    <reference type="parallel">Mc 16:15, 16.</reference>
   </title>
   <title type="parallel">Proper machine link:
    <reference type="parallel" osisRef="Mark.1.1-Mark.1.8">Mc 1:1-8</reference>
   </title>
   <verse sID="John.3.22"/>Real text<verse eID="John.3.22"/>
  </div>
 </osisText>
</osis>'''
        self.src.write_text(self.original,encoding="utf-8")

    @staticmethod
    def valid(_):
        return {"xsd_status":"validated","policy_status":"validated"}

    def test_retype_only_unlinked_parallel_refs_retaining_text_exactly(self):
        report=convert_unresolved_parallel_headings(
            self.src,self.dest,schema_proof=self.valid)
        self.assertEqual(report["text_only_parallel_reference_elements_retyped"],2)
        self.assertEqual(report["total_source_parallel_titles"],2)
        self.assertTrue(report["inverse_reconstruction_canonical_xml_byte_equal"])
        self.assertEqual(self.src.read_text(encoding="utf-8"),self.original)
        before=etree.parse(str(self.src))
        after=etree.parse(str(self.dest))
        self.assertEqual("".join(before.getroot().itertext()),
                         "".join(after.getroot().itertext()))
        refs=after.findall(".//"+OSIS+"reference")
        self.assertEqual(len(refs),1)
        self.assertEqual(refs[0].get("osisRef"),"Mark.1.1-Mark.1.8")
        segments=after.findall(".//"+OSIS+"seg")
        self.assertEqual(len(segments),2)
        self.assertTrue(all(s.get("type")==UNLINKED_SEG_TYPE for s in segments))
        self.assertEqual(report["machine_bible_links_invented"],0)

    def test_no_targets_lost_even_with_multiple_biblical_refs(self):
        self.src.write_text(self.original.replace(
            '<reference type="parallel">Jn 1:6-12, 19-34.</reference>',
            '<reference type="parallel" osisRef="John.1.6-John.1.12">Jn 1:6-12, 19-34.</reference>'),
            encoding="utf-8")
        report=convert_unresolved_parallel_headings(
            self.src,self.dest,schema_proof=self.valid)
        self.assertEqual(report["text_only_parallel_reference_elements_retyped"],1)
        self.assertEqual(len(etree.parse(str(self.dest)).findall(".//"+OSIS+"reference")),2)

    def test_unknown_source_annotation_metadata_fails_without_output(self):
        self.src.write_text(self.original.replace(
            '<reference type="parallel">Jn',
            '<reference type="parallel" resp="editor">Jn'),
            encoding="utf-8")
        with self.assertRaises(PilotError):
            convert_unresolved_parallel_headings(
                self.src,self.dest,schema_proof=self.valid)
        self.assertFalse(self.dest.exists())

    def test_xsd_rejection_does_not_leave_candidate(self):
        with self.assertRaises(PilotError):
            convert_unresolved_parallel_headings(
                self.src,self.dest,
                schema_proof=lambda _:{"xsd_status":"blocked","policy_status":"validated"})
        self.assertFalse(self.dest.exists())

    def test_unsafe_reuse_is_rejected(self):
        with self.assertRaises(PilotError):
            convert_unresolved_parallel_headings(self.src,self.src,schema_proof=self.valid)
        self.dest.write_bytes(b"existing")
        with self.assertRaises(PilotError):
            convert_unresolved_parallel_headings(self.src,self.dest,schema_proof=self.valid)
        self.assertEqual(self.dest.read_bytes(),b"existing")

    def test_no_matching_parallel_references_is_safe_noop(self):
        self.src.write_text(self.original.replace(
            '<reference type="parallel">Jn 1:6-12, 19-34.</reference>',
            '<reference type="parallel" osisRef="John.1.6">Jn 1:6-12, 19-34.</reference>'
        ).replace(
            '<reference type="parallel">Mc 16:15, 16.</reference>',
            '<reference type="parallel" osisRef="Mark.16.15">Mc 16:15, 16.</reference>'),
            encoding="utf-8")
        result=convert_unresolved_parallel_headings(
            self.src,self.dest,schema_proof=self.valid)
        self.assertEqual(result["text_only_parallel_reference_elements_retyped"],0)
        self.assertTrue(result["inverse_reconstruction_canonical_xml_byte_equal"])
        self.assertTrue(self.dest.exists())


if __name__=="__main__":
    unittest.main()
