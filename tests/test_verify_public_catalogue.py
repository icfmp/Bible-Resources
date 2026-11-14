"""Offline tests for generic live-HTTP release catalogue verifier."""
import sys
from pathlib import Path
import unittest
from hashlib import sha256
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import verify_public_catalogue as v


class PublicCatalogueVerifierTests(unittest.TestCase):
    def test_reject_external_origins_query_and_other_repo(self):
        base="https://example.org/Bible-Resources/"
        v.safe_source(base+"sword/packages/C.zip",base)
        for bad in (
            "http://example.org/Bible-Resources/sword/packages/C.zip",
            "https://other.example.org/Bible-Resources/sword/packages/C.zip",
            "https://example.org/Elsewhere/sword/packages/C.zip",
            "https://example.org/Bible-Resources/sword/packages/C.zip?tracking=1",
            "https://example.org/Bible-Resources/sword/packages/C.zip#frag",
            "https://foo:password@example.org/Bible-Resources/sword/packages/C.zip",
        ):
            with self.subTest(bad=bad), self.assertRaises(v.PublicDeliveryError):
                v.safe_source(bad,base)

    def test_verified_complete_bytes_match_expected_snapshot(self):
        base="https://example.org/Bible-Resources/"
        payload=b"Exact public ZIP payload"
        module={
            "id":"sample","sword_id":"BRTEST",
            "download":{"url":base+"sword/packages/BRTEST.zip",
                        "sha256":sha256(payload).hexdigest(),
                        "size_bytes":len(payload)},
        }
        snapshot={"repository_url":base,"schema_version":1,"modules":[module]}
        def response(url,**kwargs):
            if url.endswith("catalog/v1/catalog.json"):
                import json
                return json.dumps(snapshot).encode()
            if url.endswith("BRTEST.zip"):
                return payload
            raise AssertionError("Unexpected request")
        with patch.object(v,"read_public",side_effect=response):
            self.assertEqual(v.verify_one(snapshot,base,attempt=1,run_id="test"),["BRTEST"])
            snapshot["modules"][0]["download"]["size_bytes"]+=1
            with self.assertRaisesRegex(v.PublicDeliveryError,"hash/size"):
                v.verify_one(snapshot,base,attempt=1,run_id="test")
            snapshot["modules"][0]["download"]["size_bytes"]-=1
            snapshot["modules"][0]["download"]["sha256"]="0"*64
            with self.assertRaisesRegex(v.PublicDeliveryError,"hash/size"):
                v.verify_one(snapshot,base,attempt=1,run_id="test")

    def test_stale_public_catalogue_blocks_without_downloading(self):
        base="https://example.org/Bible-Resources/"
        expected={"repository_url":base,"modules":[{"sword_id":"BRTEST"}]}
        with patch.object(v,"read_public",return_value=b'{"modules": []}'):
            with self.assertRaisesRegex(v.PublicDeliveryError,"catalogue differs"):
                v.verify_one(expected,base,attempt=1,run_id="test")
