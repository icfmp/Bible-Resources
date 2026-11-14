"""Read-only official AndBible WebView CDP safety and no-leak tests."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_android_webview_debug import (
    _exact_local_page_debugger_url,
    _read_only_debugger_body,
    read_private_official_andbible_dom_text,
)


class OfficialAndBibleWebViewDebugTests(unittest.TestCase):
    def test_only_exact_local_forwarded_cdp_page_allowed(self):
        self.assertTrue(_exact_local_page_debugger_url(
            "ws://127.0.0.1:52655/devtools/page/ABCDEF", 52655,
        ))
        self.assertTrue(_exact_local_page_debugger_url(
            "ws://localhost:52655/devtools/page/ABCDEF", 52655,
        ))
        for candidate in (
            "ws://example.com:52655/devtools/page/ABCDEF",
            "wss://127.0.0.1:52655/devtools/page/ABCDEF",
            "ws://127.0.0.1:55555/devtools/page/ABCDEF",
            "ws://user:password@127.0.0.1:52655/devtools/page/ABCDEF",
            "ws://127.0.0.1:52655/devtools/browser/ABCDEF",
            "ws://127.0.0.1:52655/devtools/page/ABCDEF?query=bad",
            "javascript:document.body.innerText",
            "",
        ):
            self.assertFalse(_exact_local_page_debugger_url(candidate, 52655))

    def test_cdp_only_evaluates_read_only_document_body_text(self):
        with patch.dict(sys.modules, {"websocket": Mock()}) as mocked:
            fake = mocked["websocket"].create_connection.return_value
            fake.recv.return_value = json.dumps({
                "id": 1,
                "result": {"result": {"type": "string", "value": "Private genuine text"}},
            })
            got = _read_only_debugger_body(
                "ws://127.0.0.1:52655/devtools/page/abc", 52655,
            )
        self.assertEqual(got, "Private genuine text")
        sent = json.loads(fake.send.call_args.args[0])
        self.assertEqual(sent["method"], "Runtime.evaluate")
        self.assertEqual(sent["params"]["expression"],
                         'document.body ? document.body.innerText : ""')
        self.assertTrue(sent["params"]["returnByValue"])
        self.assertNotIn("set", sent["params"]["expression"])
        fake.close.assert_called_once()

    @patch("commentary_android_webview_debug._read_only_debugger_body")
    @patch("commentary_android_webview_debug.build_opener")
    @patch("commentary_android_webview_debug.adb")
    def test_only_verified_android_process_socket_yields_private_dom(
        self, adb, build_opener, debugger,
    ):
        def device(*args, **kwargs):
            if args[:3] == ("shell", "pidof", "net.bible.android.activity"):
                return b"12345\n"
            if args[:3] == ("shell", "cat", "/proc/net/unix"):
                return b"one socket: @webview_devtools_remote_12345\n"
            if args[:3] == ("forward", "tcp:0", "localabstract:webview_devtools_remote_12345"):
                return b"52655\n"
            if args[:3] == ("forward", "--remove", "tcp:52655"):
                return b""
            return b""
        adb.side_effect = device
        resource = Mock()
        resource.read.return_value = json.dumps([
            {"type": "page",
             "webSocketDebuggerUrl": "ws://127.0.0.1:52655/devtools/page/abc"},
            {"type": "page",
             "webSocketDebuggerUrl": "ws://external.invalid:52655/devtools/page/def"},
        ]).encode()
        response = MagicMock()
        response.__enter__.return_value = resource
        build_opener.return_value.open.return_value = response
        debugger.return_value = "Private authentic commentary text"
        texts, meta = read_private_official_andbible_dom_text()
        self.assertEqual(texts, ["Private authentic commentary text"])
        self.assertEqual(meta["actual_Android_debug_page_targets_discovered"], 1)
        self.assertEqual(meta["actual_Android_debug_DOM_pages_read"], 1)
        self.assertEqual(meta["status"], "official_Android_reader_DOM_text_read_privately")
        self.assertNotIn("Private authentic", str(meta))
        self.assertFalse(meta["Android_DOM_page_URL_words_XML_screenshot_or_cookies_exported"])
        self.assertTrue(any(
            call.args[:3] == ("forward", "--remove", "tcp:52655")
            for call in adb.call_args_list
        ))

    @patch("commentary_android_webview_debug.adb", return_value=b"")
    def test_no_official_debug_socket_is_inconclusive(self, adb):
        texts, meta = read_private_official_andbible_dom_text()
        self.assertEqual(texts, [])
        self.assertFalse(meta["actual_app_debug_socket_found"])
        self.assertEqual(meta["status"], "inconclusive_original_app_WebView_debug_unavailable")


if __name__ == "__main__":
    unittest.main()
