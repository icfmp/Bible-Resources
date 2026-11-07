"""Offline source downloader and XSD provenance tests."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pilot_fetch import PilotError, SafeRedirect, fetch, validate_url
from probe_official_osis import inspect_bytes
from validate import DRIVERS, ALLOWED


class FakeResponse:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload
        self.off = 0

    def read(self, count=-1):
        if count < 0:
            count = len(self.payload) - self.off
        block = self.payload[self.off:self.off+count]
        self.off += len(block)
        return block

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, url, payload):
        self.url, self.payload = url, payload

    def open(self, request, timeout):
        return FakeResponse(self.url, self.payload)


class PreparationTests(unittest.TestCase):
    def test_https_allowlist_blocks_arbitrary_mirrors_and_redirects(self):
        for url in ("http://ebible.org/sword/zip/test.zip",
                    "https://evil.example.net/Scriptures/x.zip",
                    "https://ebible.org.evil.test/path",
                    "https://ebible.org:8443/Scriptures/x.zip",
                    "https://evil.example.net@bad.test/x"):
            with self.subTest(url=url):
                with self.assertRaises(PilotError):
                    validate_url(url, "lsg")
        validate_url("https://ebible.org/Scriptures/fraLSG_usfm.zip", "lsg")
        validate_url("https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/MHC.zip", "mhc")
        with self.assertRaises(PilotError):
            SafeRedirect("lsg").redirect_request(
                None, None, 302, "moved", {}, "http://ebible.org/sword/zip/test.zip"
            )

    def test_fetch_does_not_overwrite_or_leave_temp_artifacts(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "sword.zip"
            url = "https://ebible.org/sword/zip/fraLSG1910eb.zip"
            payload = b"demo zip bytes"
            result = fetch(url, path, "lsg", opener=FakeOpener(url, payload))
            self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(path.read_bytes(), payload)
            with self.assertRaisesRegex(PilotError, "overwrite"):
                fetch(url, path, "lsg", opener=FakeOpener(url, b"replacement"))
            self.assertEqual(list(Path(root).glob(".pilot-*")), [])

    def test_fetch_rejects_final_redirect_and_preserves_destination(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "sword.zip"
            url = "https://ebible.org/sword/zip/fraLSG1910eb.zip"
            with self.assertRaises(PilotError):
                fetch(url, path, "lsg",
                      opener=FakeOpener("https://untrusted.example.com/a.zip", b"no"))
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_schema_parser_checks_deps_without_loading_external_urls(self):
        schema = (b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
                  b'targetNamespace="urn:test"><xs:element name="r" '
                  b'type="xs:string"/></xs:schema>')
        found = inspect_bytes(schema)
        self.assertTrue(found["ready_to_pin"])
        self.assertEqual(found["sha256"], hashlib.sha256(schema).hexdigest())
        with_deps = schema.replace(b'<xs:element', b'<xs:import namespace="urn:other" '
                                    b'schemaLocation="https://example.org/other.xsd"/>'
                                    b'<xs:element')
        found = inspect_bytes(with_deps)
        self.assertFalse(found["ready_to_pin"])
        self.assertEqual(found["schema_dependencies"][0]["kind"], "import")

    def test_mhc_zcom4_supported_by_repository_publisher(self):
        self.assertIn("zCom4", DRIVERS)
        self.assertIn("zCom4", ALLOWED["commentary"])
        self.assertNotIn("zCom4", ALLOWED["bible"])


if __name__ == "__main__":
    unittest.main()
