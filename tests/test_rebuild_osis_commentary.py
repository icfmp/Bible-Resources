#!/usr/bin/env python3
"""Offline tests for generic private OSIS-to-SWORD phase one."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from rebuild_osis_commentary import RebuildFailure, build, source_census

ORIGINAL = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
    b'<osisText osisIDWork="Trial" xml:lang="fr">'
    b'<div type="book" osisID="Gen">'
    b'<div type="section" annotateType="commentary" annotateRef="Gen.1.1">'
    b'<p>Un mot accentu\xc3\xa9 ; ponctuation \xe2\x80\x94 et texte.</p>'
    b'</div></div></osisText></osis>'
)


class SourceStageOneTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.path = Path(self.scratch.name) / "source.osis.xml"

    def test_valid_unicode_source_bytes_are_untouched(self):
        self.path.write_bytes(ORIGINAL)
        digest = hashlib.sha256(ORIGINAL).hexdigest()
        report = source_census(self.path, digest)
        self.assertEqual(report["source_sha256"], digest)
        self.assertEqual(report["source_language_declared"], "fr")
        self.assertEqual(report["source_bytes"], len(ORIGINAL))
        self.assertEqual(report["osis_reference_elements"], 0)
        self.assertEqual(self.path.read_bytes(), ORIGINAL)

    def test_refuses_any_digest_mismatch(self):
        self.path.write_bytes(ORIGINAL)
        with self.assertRaises(RebuildFailure):
            source_census(self.path, hashlib.sha256(b"other").hexdigest())

    def test_refuses_doctype_and_entity_injection(self):
        malicious = (b'<!DOCTYPE osis [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
                     + ORIGINAL.replace(b'Un mot', b'&x; Un mot'))
        self.path.write_bytes(malicious)
        with self.assertRaises(RebuildFailure):
            source_census(self.path, hashlib.sha256(malicious).hexdigest())

    def test_refuses_non_osis_document(self):
        alien = b"<root><osisText><div/></osisText></root>"
        self.path.write_bytes(alien)
        with self.assertRaises(RebuildFailure):
            source_census(self.path, hashlib.sha256(alien).hexdigest())

    def test_language_format_is_not_english_specific(self):
        self.path.write_bytes(ORIGINAL)
        with self.assertRaises(RebuildFailure):
            build(self.path, hashlib.sha256(ORIGINAL).hexdigest(),
                  Path(self.scratch.name) / "fresh",
                  module="MHCStage1", lang="english", versification="KJV",
                  native_reader=Path(self.scratch.name) / "reader")


if __name__ == "__main__":
    unittest.main()
