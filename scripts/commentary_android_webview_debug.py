#!/usr/bin/env python3
"""PRIVATE read-only DOM text from the official AndBible WebView debug socket.

The pinned official production-1117 BibleView.kt explicitly enables
WebView.setWebContentsDebuggingEnabled(true), even in its release APK.
A local Android debug socket and loopback CDP read-only Runtime.evaluate
may expose the actual rendered document where uiautomator does not.
Never print/export a page URL, DOM, text, screenshot, cookie, or token.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler

from pilot_preflight import PilotError
from probe_andbible_android_emulator import PACKAGE, adb

MAX_CDP_BODY = 256_000
MAX_TARGETS = 8


def _exact_local_page_debugger_url(uri: str, port: int) -> bool:
    if not isinstance(uri, str) or len(uri) > 500:
        return False
    try:
        parsed = urlsplit(uri)
        return (
            parsed.scheme == "ws"
            and parsed.hostname in ("localhost", "127.0.0.1")
            and parsed.port == port
            and parsed.path.startswith("/devtools/page/")
            and len(parsed.path) <= 180
            and parsed.query == ""
            and parsed.fragment == ""
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def _read_only_debugger_body(url: str, port: int) -> str:
    """Read document.body.innerText, and NOTHING with side effects."""
    if not _exact_local_page_debugger_url(url, port):
        raise PilotError("Untrusted WebView CDP loopback URL")
    # Only the pinned CI runner's Android job installs this small client.
    # Unit tests of safety and transcript parsing need no third-party socket.
    import websocket
    connection = websocket.create_connection(
        url, timeout=8, origin="http://localhost",
    )
    try:
        connection.settimeout(8)
        connection.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": 'document.body ? document.body.innerText : ""',
                "returnByValue": True,
                "awaitPromise": False,
            },
        }))
        for _ in range(16):
            payload = connection.recv()
            if not isinstance(payload, str) or len(payload) > MAX_CDP_BODY + 100_000:
                raise PilotError("Unbounded private WebView debugger response")
            message = json.loads(payload)
            if not isinstance(message, dict) or message.get("id") != 1:
                continue
            value = message.get("result", {}).get("result", {}).get("value")
            return value if isinstance(value, str) and len(value) <= MAX_CDP_BODY else ""
        return ""
    finally:
        connection.close()


def read_private_official_andbible_dom_text() -> tuple[list[str], dict]:
    """Try the *actual official app process's* local WebView CDP endpoints.

    Status is NOT a prose PASS. Callers must match at least sixteen original
    source words against the independently SHA-attested full SWORD corpus.
    """
    result = {
        "scope": "official_AndBible_pinned_release_read_only_loopback_WebView_CDP",
        "actual_app_debug_socket_found": False,
        "actual_Android_debug_page_targets_discovered": 0,
        "actual_Android_debug_DOM_pages_read": 0,
        "status": "inconclusive_original_app_WebView_debug_unavailable",
        "Android_DOM_page_URL_words_XML_screenshot_or_cookies_exported": False,
    }
    pids = adb("shell", "pidof", PACKAGE, timeout=20, fail=False).strip()
    if not re.fullmatch(rb"[1-9][0-9]{1,8}", pids):
        return [], result
    socket = "webview_devtools_remote_" + pids.decode("ascii")
    sockets = adb("shell", "cat", "/proc/net/unix", timeout=20, fail=False)
    if not any(
        line.split() and line.split()[-1] == ("@" + socket).encode("ascii")
        for line in sockets.splitlines()
    ):
        return [], result
    result["actual_app_debug_socket_found"] = True
    port_text = adb(
        "forward", "tcp:0", "localabstract:" + socket, timeout=15, fail=False,
    ).strip()
    if not re.fullmatch(rb"[0-9]{4,5}", port_text):
        return [], result
    port = int(port_text)
    if not 1024 <= port <= 65535:
        return [], result
    try:
        # Disallow all proxy use; only the locally forwarded Android debugger
        # at a verified loopback URL is reachable by this private probe.
        opener = build_opener(ProxyHandler({}))
        with opener.open("http://127.0.0.1:%d/json" % port, timeout=8) as response:
            data = response.read(MAX_CDP_BODY + 1)
        if len(data) > MAX_CDP_BODY:
            raise PilotError("Oversized private Android WebView page listing")
        records = json.loads(data)
        if not isinstance(records, list) or len(records) > 30:
            raise PilotError("Unbounded real Android WebView debugger target list")
        pages = [
            item for item in records
            if isinstance(item, dict)
            and item.get("type") == "page"
            and _exact_local_page_debugger_url(
                item.get("webSocketDebuggerUrl"), port,
            )
        ][:MAX_TARGETS]
        result["actual_Android_debug_page_targets_discovered"] = len(pages)
        texts = []
        for page in pages:
            try:
                body = _read_only_debugger_body(
                    page["webSocketDebuggerUrl"], port,
                )
            except (ValueError, OSError, TimeoutError, ImportError, PilotError):
                continue
            if body.strip():
                texts.append(body)
        result["actual_Android_debug_DOM_pages_read"] = len(texts)
        result["status"] = (
            "official_Android_reader_DOM_text_read_privately"
            if texts else "inconclusive_Android_debug_socket_no_readable_DOM"
        )
        return texts, result
    except (ValueError, OSError, TimeoutError, json.JSONDecodeError, PilotError):
        result["status"] = "inconclusive_Android_debug_socket_no_readable_DOM"
        return [], result
    finally:
        # Never expose the private page-debugger to the Internet or leave any
        # Android ADB forwarding in the runner after this bounded test.
        adb("forward", "--remove", "tcp:%d" % port, timeout=15, fail=False)
