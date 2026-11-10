"""Offline tests for guarded publisher OSIS observation and privacy."""
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from publisher_osis_observation import (
    _source_config, _verified_url, _download, inspect_official_osis,
    PublisherOSISObservationError,
)

URL = "https://cdn.editeurbpc.com/bible/osis/JND/bible_jnd_2_0.xml"


def example(note_marker="a"):
    n = f' n="{note_marker}"' if note_marker is not None else ""
    return (
        '<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
        '<osisText osisIDWork="TEST"><div type="book" osisID="Gen">'
        '<verse osisID="Gen.1.1">PRIVATE SCRIPTURE '
        '<note type="translation"' + n + '>PRIVATE NOTE</note>'
        ' NEVER RELEASE.</verse></div></osisText></osis>'
    ).encode("utf-8")


class FakeResponse(io.BytesIO):
    def geturl(self):
        return URL


class FakeOpener:
    def __init__(self,data):
        self.data=data
    def open(self,request,timeout=90):
        return FakeResponse(self.data)


class PublisherOSISObservationTests(unittest.TestCase):
    def test_known_reviewed_publisher_edition(self):
        cfg = _source_config("frajnd-2024")
        self.assertEqual(cfg["official_source_url"],URL)
        self.assertEqual(cfg["status"],"research_only")

    def test_reject_unapproved_urls_and_resource_ids(self):
        for x in (
            "http://cdn.editeurbpc.com/bible/osis/JND/test.xml",
            "https://evil.example.com/data.xml",
            "https://cdn.editeurbpc.com/../private.xml",
            "https://cdn.editeurbpc.com/file.xml?secret=foo",
            "https://cdn.editeurbpc.com/file.zip",
            "https://user:pass@cdn.editeurbpc.com/file.xml",
        ):
            with self.subTest(x=x),self.assertRaises(PublisherOSISObservationError):
                _verified_url(x)
        for x in ("../evil","unknown","bad%2fresource",""):
            with self.subTest(x=x),self.assertRaises(PublisherOSISObservationError):
                _source_config(x)

    def test_note_markers_count_without_literal_text_or_callers(self):
        out=inspect_official_osis(example("a"))
        self.assertEqual(out["source_note_caller_shape_counts"],{
            "single_lowercase_ascii_letter":1
        })
        self.assertEqual(out["source_element_counts"]["verse"],1)
        self.assertEqual(out["source_note_type_allowlisted_counts"]["translation"],1)
        self.assertFalse(out["source_note_labels_equal_to_usfx_verified"])
        for secret in ("PRIVATE","SCRIPTURE","NEVER RELEASE"):
            self.assertNotIn(secret,json.dumps(out))

    def test_missing_caller_is_not_assumed_intact(self):
        out=inspect_official_osis(example(None))
        self.assertEqual(out["source_note_caller_shape_counts"],{"absent":1})

    def test_other_note_markers_require_review(self):
        out=inspect_official_osis(example("TOP_SECRET"))
        self.assertEqual(out["source_note_caller_shape_counts"],{
            "other_unreviewed_literal":1
        })
        self.assertNotIn("TOP_SECRET",json.dumps(out))

    def test_reject_doctype_dtd_or_wrong_root(self):
        for xml in (
            b'<!DOCTYPE osis [<!ENTITY x SYSTEM "file:///etc/passwd">]>'+example(),
            b'<private_root><verse/></private_root>',
            b'<osis><osisText>no numbered verse</osisText></osis>',
            b'<osis><verse>bad',
        ):
            with self.subTest(start=xml[:15]),self.assertRaises(
                PublisherOSISObservationError):
                inspect_official_osis(xml.ljust(128,b" "))

    def test_download_is_bounded_and_provenance_url_checked(self):
        xml=example()
        self.assertEqual(_download(URL,opener=FakeOpener(xml)),xml)
        with self.assertRaises(PublisherOSISObservationError):
            _download(URL,opener=FakeOpener(b"not XML"))

if __name__=="__main__":
    unittest.main()
