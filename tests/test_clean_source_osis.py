#!/usr/bin/env python3
"""Language-neutral, synthetic checks for private OSIS source cleanup."""
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from lxml import etree

from clean_source_osis import CleanupError, clean


OSIS = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText osisIDWork="Fixture" xml:lang="fr">
    <div type="book" osisID="Gen">
      <title>  L'Évangile  </title>
      <div type="section" annotateType="commentary" annotateRef="Gen.1.1">
        <p>Grâce  fidèle — paix.</p>
        <p>Keep ** and \\*  as is.</p>
        <p>Keep <note n="*"><p>note  has double spaces</p></note> here.</p>
        <p><reference osisRef="Gen.1.2">Un  renvoi</reference></p>
      </div>
    </div>
  </osisText>
</osis>
""".encode("utf-8")


class CleanSourceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / "source.xml"
        self.output = self.root / "cleaned.xml"
        self.source.write_bytes(OSIS)
        self.digest = sha256(OSIS).hexdigest()

    def test_preserves_notes_references_marks_and_accents(self):
        result = clean(self.source, self.digest, output=self.output)
        self.assertEqual(self.source.read_bytes(), OSIS)
        data = self.output.read_bytes()
        self.assertIn("Grâce fidèle".encode("utf-8"), data)
        self.assertIn(b"Keep ** and \\*  as is.", data)
        self.assertIn(b"note  has double spaces", data)
        self.assertIn(b"Un  renvoi", data)
        self.assertIn(b"annotateRef=\"Gen.1.1\"", data)
        self.assertEqual(result["cleanup_changes"]["changed_plain_nodes"], 2)
        self.assertTrue(result["all_note_and_reference_text_preserved"])
        self.assertFalse(result["published"])
        root = etree.fromstring(data)
        refs = [node for node in root.iter()
                if isinstance(node.tag, str) and node.tag.endswith("}reference")]
        self.assertEqual(refs[0].get("osisRef"), "Gen.1.2")

    def test_audit_only_does_not_write_output(self):
        result = clean(self.source, self.digest)
        self.assertFalse(result["cleaned_file_written_privately"])
        self.assertFalse(self.output.exists())

    def test_rejects_stale_source(self):
        with self.assertRaises(CleanupError):
            clean(self.source, sha256(b"other").hexdigest(), output=self.output)

    def test_rejects_overwriting_original_or_candidate(self):
        with self.assertRaises(CleanupError):
            clean(self.source, self.digest, output=self.source)
        self.output.write_bytes(b"do not overwrite")
        with self.assertRaises(CleanupError):
            clean(self.source, self.digest, output=self.output)

    def test_rejects_entities(self):
        raw = OSIS.replace(
            b'<osis xmlns=', b'<!DOCTYPE osis [<!ENTITY x SYSTEM "file:///etc/passwd">]><osis xmlns=')
        self.source.write_bytes(raw)
        with self.assertRaises(CleanupError):
            clean(self.source, sha256(raw).hexdigest())

    def test_unmodified_source_stays_byte_identical(self):
        raw = OSIS.replace("Grâce  fidèle".encode("utf-8"),
            "Grâce fidèle".encode("utf-8")).replace(
            "<title>  L'Évangile  </title>".encode("utf-8"),
            "<title>L'Évangile</title>".encode("utf-8"))
        self.source.write_bytes(raw)
        clean(self.source, sha256(raw).hexdigest(), output=self.output)
        self.assertEqual(raw, self.output.read_bytes())


if __name__ == "__main__":
    unittest.main()
