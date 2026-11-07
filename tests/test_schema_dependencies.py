"""Offline test: CrossWire XSD imports only reviewed W3C xml.xsd bytes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from guard_osis import _schema, StructureFailure

XSD = "http://www.w3.org/2001/XMLSchema"
XMLNS = "http://www.w3.org/XML/1998/namespace"
MAIN = f"""<xs:schema xmlns:xs="{XSD}" xmlns:xml="{XMLNS}"
  targetNamespace="urn:example">
  <xs:import namespace="{XMLNS}" schemaLocation="http://www.w3.org/2001/xml.xsd"/>
  <xs:element name="osis">
    <xs:complexType><xs:attribute ref="xml:lang" use="optional"/></xs:complexType>
  </xs:element>
</xs:schema>""".encode()
DEPENDENCY = f"""<xs:schema xmlns:xs="{XSD}" targetNamespace="{XMLNS}">
  <xs:attribute name="lang" type="xs:string"/>
</xs:schema>""".encode()


class ReviewedSchemaDependencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.main = root / "osis.xsd"
        self.dep = root / "xml.xsd"
        self.main.write_bytes(MAIN)
        self.dep.write_bytes(DEPENDENCY)
        self.policy = {
            "schema_status": "reviewed",
            "schema_sha256": hashlib.sha256(MAIN).hexdigest(),
            "schema_dependencies": [{
                "namespace": XMLNS,
                "schema_location": "http://www.w3.org/2001/xml.xsd",
                "local_filename": "xml.xsd",
                "sha256": hashlib.sha256(DEPENDENCY).hexdigest(),
            }],
        }

    def test_local_dependency_compiles_without_network_access(self):
        schema, sha = _schema(self.policy, self.main)
        self.assertEqual(sha, self.policy["schema_sha256"])
        self.assertIsNotNone(schema)

    def test_changed_dependency_cannot_be_silently_used(self):
        self.dep.write_bytes(DEPENDENCY + b"<!-- corrupted -->")
        with self.assertRaises(StructureFailure) as exc:
            _schema(self.policy, self.main)
        self.assertEqual(exc.exception.code, "SCHEMA_DEPENDENCY_HASH_MISMATCH")

    def test_missing_dependency_blocks(self):
        self.dep.unlink()
        with self.assertRaises(StructureFailure) as exc:
            _schema(self.policy, self.main)
        self.assertEqual(exc.exception.code, "SCHEMA_DEPENDENCY_MISSING")

    def test_unreviewed_import_blocks_even_if_downloadable(self):
        content = MAIN.replace(b"http://www.w3.org/2001/xml.xsd",
                               b"https://untrusted.example.net/custom.xsd")
        self.main.write_bytes(content)
        self.policy["schema_sha256"] = hashlib.sha256(content).hexdigest()
        with self.assertRaises(StructureFailure) as exc:
            _schema(self.policy, self.main)
        self.assertEqual(exc.exception.code, "SCHEMA_DEPENDENCY_UNREVIEWED")


if __name__ == "__main__":
    unittest.main()
