"""Regression tests for owner-authorized, source-bound verse-index compromises.

All examples are made-up text and references, not production exceptions.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from reviewed_reference_merges import (load_reviewed_merges,assess_reviewed_merges,
                                       annotate_editorial_label)
from pilot_preflight import PilotError

class ReviewedMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.original=b"synthetic source identity"
        self.digest=hashlib.sha256(self.original).hexdigest()
        self.keys=[("ABC",1,1),("ABC",1,2),("ABC",1,3)]
        self.record={
            "schema_version":1,
            "source_edition":"synthetic example",
            "source_format":"USFX",
            "source_document_sha256":self.digest,
            "versification":"Segond",
            "policy":"approved_explicit_temporary_adjacent_verse_index_merge",
            "authorization":{"who":"Bible Resources project owner",
                "date":"2026-11-08", "record":"Explicitly reviewed synthetic fixture",
                "scope":"Only the index, never Scripture words"},
            "allowed_merges":[{
                "authorial_source_key":"ABC.1.3",
                "reader_source_key":"ABC.1.2",
                "osis_source_key":"Mark.1.3",
                "osis_reader_key":"Mark.1.2",
                "preferred_display_label":"2–3",
                "reason":"The installed SWORD index has no third verse for this chapter.",
                "source_content_preserved":True,
                "independent_reference_access_lost":True,
                "reversible":True,
                "status":"temporarily_authorized_versification_compromise"
            }]
        }
        self.path=self.root/"policy.json"
        self.write()
    def write(self):
        self.path.write_text(json.dumps(self.record),encoding="utf-8")
    def load(self):
        return load_reviewed_merges(self.path,source_digest=self.digest,
                                    source_keys=self.keys,versification="Segond")
    def assessment(self):
        return {
            "status":"stock_segond_limitations_classified_not_approved",
            "all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks":True,
            "all_reference_differences_explained":True,
            "original_source_modified":False,
            "full_compiled_notes_poetry_markup_verified":False,
            "source_only_verse_count":1,
            "appended_source_keys":[{
                "book":"ABC","chapter":1,"source_verse":3,
                "compiled_verse":2,"distinct_original_reference_unavailable":True
            }]
        }
    def test_exactly_authorized_verified_merge_can_pass_index_review_only(self):
        decisions,digest=self.load()
        result=assess_reviewed_merges(decisions,digest,self.assessment())
        self.assertEqual(result["status"],"source_bound_owner_authorized_index_compromise")
        self.assertEqual(result["authorized_merge_count"],1)
        self.assertFalse(result["module_approved_for_publication"])
        self.assertTrue(result["full_compiled_markup_not_yet_verified"])
        self.assertTrue(result["versification_index_not_exact"])
    def test_changed_source_or_different_registry_rejected(self):
        with self.assertRaises(PilotError):
            load_reviewed_merges(self.path,source_digest="f"*64,
                                 source_keys=self.keys,versification="Segond")
        with self.assertRaises(PilotError):
            load_reviewed_merges(self.path,source_digest=self.digest,
                                 source_keys=self.keys,versification="NRSV")
    def test_nonadjacent_missing_or_internal_verse_rejected(self):
        for source,dest,keys in [
            ("ABC.1.3","ABC.1.1",self.keys),
            ("ABC.1.4","ABC.1.3",self.keys),
            ("ABC.1.3","ABC.1.2",self.keys+[("ABC",1,4)]),
        ]:
            with self.subTest(source=source,dest=dest,keys=keys):
                self.record["allowed_merges"][0]["authorial_source_key"]=source
                self.record["allowed_merges"][0]["reader_source_key"]=dest
                self.write()
                with self.assertRaises(PilotError):
                    load_reviewed_merges(self.path,source_digest=self.digest,
                                         source_keys=keys,versification="Segond")
    def test_any_unreviewed_extra_append_or_text_loss_stays_blocked(self):
        decisions,digest=self.load()
        invalid=self.assessment()
        invalid["appended_source_keys"].append({
            "book":"XYZ","chapter":2,"source_verse":5,
            "compiled_verse":4,"distinct_original_reference_unavailable":True
        })
        with self.assertRaises(PilotError):
            assess_reviewed_merges(decisions,digest,invalid)
        invalid=self.assessment()
        invalid["all_source_character_streams_preserved_modulo_whitespace_and_reader_asterisks"]=False
        with self.assertRaises(PilotError):
            assess_reviewed_merges(decisions,digest,invalid)
        invalid=self.assessment()
        invalid["appended_source_keys"][0]["compiled_verse"]=1
        with self.assertRaises(PilotError):
            assess_reviewed_merges(decisions,digest,invalid)
    def test_invalid_label_or_lack_of_owner_review_is_blocked(self):
        self.record["allowed_merges"][0]["preferred_display_label"]="1–3"
        self.write()
        with self.assertRaises(PilotError):
            self.load()
        self.record["allowed_merges"][0]["preferred_display_label"]="2–3"
        self.record["authorization"]["who"]="UNKNOWN"
        self.write()
        with self.assertRaises(PilotError):
            self.load()
    def test_isolated_osis_n_label_preserves_all_authorial_words(self):
        self.record["allowed_merges"][0]["preferred_display_label"]="2–3"
        self.write()
        decisions,_=self.load()
        self.source=self.root/"source.xml"
        self.target=self.root/"result.xml"
        raw=('<?xml version="1.0" encoding="utf-8"?>'
             '<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
             '<verse osisID="Mark.1.2" sID="Mark.1.2"/>'
             'Authorial text with all punctuation.'
             '<verse eID="Mark.1.2"/>'
             '<verse osisID="Mark.1.3" sID="Mark.1.3"/>'
             'Other words.'
             '<verse eID="Mark.1.3"/></osis>')
        self.source.write_text(raw,encoding="utf-8")
        before=self.source.read_bytes()
        report=annotate_editorial_label(
            self.source,self.target,decisions,
            schema_proof=lambda path:{"xsd_status":"validated","policy_status":"validated"})
        self.assertEqual(self.source.read_bytes(),before)
        self.assertFalse(report["labels_rendered_by_all_sword_readers"])
        self.assertTrue(report["no_inline_label_added_to_scripture"])
        tree=etree.parse(str(self.target))
        ns={"o":"http://www.bibletechnologies.net/2003/OSIS/namespace"}
        v=tree.xpath(".//o:verse[@osisID='Mark.1.2']",namespaces=ns)
        self.assertEqual(len(v),1)
        self.assertEqual(v[0].get("n"),"2–3")
        self.assertEqual("".join(tree.getroot().itertext()),
                         "Authorial text with all punctuation.Other words.")
        with self.assertRaises(PilotError):
            annotate_editorial_label(
                self.source,self.target,decisions,
                schema_proof=lambda path:{"xsd_status":"validated","policy_status":"validated"})
    def test_schema_rejection_of_label_is_blocking(self):
        decisions,_=self.load()
        p=self.root/"in.xml";out=self.root/"out.xml"
        p.write_text('<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
                     '<verse osisID="Mark.1.2" sID="Mark.1.2"/>x'
                     '<verse eID="Mark.1.2"/></osis>')
        with self.assertRaises(PilotError):
            annotate_editorial_label(p,out,decisions,
                schema_proof=lambda path:{"xsd_status":"blocked","policy_status":"not_run"})

if __name__=="__main__":
    unittest.main()
