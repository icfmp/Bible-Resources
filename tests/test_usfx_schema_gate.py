"""Exact official USFX XSD provenance must fail closed; never leak publisher text."""
from hashlib import sha256
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from usfx_schema_gate import (
    examine_schema, observe_schema, validate_source_with_pinned_schema,
    USFXSchemaError, XSD_URL,
)

XSD = (b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
       b'<xs:element name="usfx" type="xs:anyType"/>'
       b'</xs:schema>')
SOURCE = b'<usfx><book id="GEN"><c id="1"/><v id="1"/>SECRET SCRIPTURE</book></usfx>'


class OfficialUSFXSchemaTests(unittest.TestCase):
    def test_observed_schema_is_not_automatically_approved(self):
        receipt = observe_schema(XSD)
        self.assertEqual(receipt["official_xsd_sha256"], sha256(XSD).hexdigest())
        self.assertFalse(receipt["schema_pinned_and_reviewed"])
        self.assertTrue(receipt["offline_compiled_without_external_dependencies"])

    def test_reviewed_exact_sha_validates_source_without_exposing_text(self):
        policy={"schema_status":"reviewed","download_url":XSD_URL,
                "sha256":sha256(XSD).hexdigest()}
        result = validate_source_with_pinned_schema(SOURCE,XSD,policy)
        self.assertTrue(result["official_usfx_schema_validated"])
        self.assertEqual(result["status"], "official_usfx_xsd_validated")
        self.assertNotIn("SECRET",str(result))
        self.assertFalse(result["published"])

    def test_schema_drift_and_missing_review_never_validate(self):
        for policy in (
            {"schema_status":"observed","download_url":XSD_URL,
             "sha256":sha256(XSD).hexdigest()},
            {"schema_status":"reviewed","download_url":XSD_URL,"sha256":"0"*64},
            {"schema_status":"reviewed","download_url":"https://other.example/xsd",
             "sha256":sha256(XSD).hexdigest()},
        ):
            with self.subTest(policy=policy),self.assertRaises(USFXSchemaError):
                validate_source_with_pinned_schema(SOURCE,XSD,policy)

    def test_schema_parser_blocks_remote_includes_and_dtds(self):
        includes=(b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                  b'<xs:include schemaLocation="https://evil.example/file.xsd"/>'
                  b'<xs:element name="usfx" type="xs:anyType"/></xs:schema>')
        dtd=b'<!DOCTYPE xs:schema [<!ENTITY x "bad">]>'+XSD
        for payload in (includes,dtd,b'<not-schema/>'):
            with self.subTest(payload=payload),self.assertRaises(USFXSchemaError):
                examine_schema(payload)

    def test_incorrect_source_root_is_never_silently_converted(self):
        policy={"schema_status":"reviewed","download_url":XSD_URL,
                "sha256":sha256(XSD).hexdigest()}
        with self.assertRaises(ValueError):
            validate_source_with_pinned_schema(b'<other/>',XSD,policy)


if __name__ == "__main__":
    unittest.main()
