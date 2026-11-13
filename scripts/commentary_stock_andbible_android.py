#!/usr/bin/env python3
"""Research-only Android AndBible import of an unchanged SHA-pinned zCom ZIP.

Only acts on controls actually returned by a bounded Android UI hierarchy.
Never treats a click, a resolved deep link or a screenshot as proof that the
original commentary text or links rendered faithfully. No screenshots,
source words, native ZIP, UI hierarchy or log files leave the runner.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from commentary_intake import load_manifest
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from probe_andbible_android_emulator import APK_SHA256, PACKAGE, adb

MODULE = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,39}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
BOUNDS = re.compile(r"\[(\d{1,4}),(\d{1,4})\]\[(\d{1,4}),(\d{1,4})\]\Z")
SAFE = frozenset({
    "LOAD DOCUMENTS FROM FILES", "LOAD DOCUMENT FROM FILES", "ADVANCED",
    "DOWNLOADS", "DOWNLOAD", "PROCEED", "BROWSE FILES", "BROWSE",
    "IMPORT", "INSTALL", "OK", "OPEN", "CONTINUE", "DONE",
    "DISMISS", "DISMISS UNTIL NEXT UPDATE", "ALLOW",
    "WHILE USING THE APP", "USE THIS FOLDER", "WAIT", "CLOSE APP",
})


def safe_controls(xml: bytes, module_id: str, title: str) -> dict:
    """Whitelist buttons and exact source metadata, never arbitrary reader text."""
    if (not isinstance(xml, bytes) or len(xml) > 3_000_000
            or not MODULE.fullmatch(module_id)
            or not isinstance(title, str) or not 1 <= len(title) <= 180):
        raise PilotError("Unsafe Android screen or commentary metadata")
    try:
        tree = ET.fromstring(xml)
    except ET.ParseError:
        return {"controls": [], "reader_module_metadata_detected": False}
    file_label = module_id.upper() + ".ZIP"
    # Never dismiss an arbitrary application. On hosted AOSP emulators only,
    # the known launcher ANR may be closed using an explicitly seen control.
    launcher_anr = any(
        node.attrib.get("text", "").strip().casefold() in {
            "pixel launcher isn't responding", "quickstep isn't responding"
        } for node in tree.iter("node")
    )
    results = []
    module_label_in_tree = False
    for node in tree.iter("node"):
        candidates = (node.attrib.get("text", ""), node.attrib.get("content-desc", ""))
        for value in candidates:
            # Source metadata identity only, not user-authored or rendered prose.
            if value.strip().casefold() in (module_id.casefold(), title.casefold()):
                module_label_in_tree = True
            label = value.strip().upper()
            if label not in SAFE and label != file_label:
                continue
            if label == "CLOSE APP" and not launcher_anr:
                continue
            match = BOUNDS.fullmatch(node.attrib.get("bounds", ""))
            if not match:
                continue
            x1, y1, x2, y2 = map(int, match.groups())
            if not (0 <= x1 < x2 <= 1600 and 0 <= y1 < y2 <= 2400):
                continue
            item = {"action": "EXACT_MODULE_ZIP" if label == file_label else label,
                    "x": (x1+x2)//2, "y": (y1+y2)//2}
            if item not in results:
                results.append(item)
    return {"controls": results[:60], "reader_module_metadata_detected": module_label_in_tree}


def _screen(module_id: str, title: str) -> dict:
    adb("shell", "uiautomator", "dump", "/sdcard/commentary-stock-import-ui.xml",
        timeout=40, fail=False)
    data = adb("exec-out", "cat", "/sdcard/commentary-stock-import-ui.xml",
               timeout=20, fail=False)
    return safe_controls(data, module_id, title)


def _tap(controls: list[dict], choices: tuple[str, ...]) -> str | None:
    for choice in choices:
        if choice not in SAFE and choice != "EXACT_MODULE_ZIP":
            raise PilotError("Unreviewed Android command")
        for item in controls:
            if item["action"] == choice:
                adb("shell", "input", "tap", str(item["x"]), str(item["y"]), timeout=15)
                time.sleep(3)
                return choice
    return None


def _start_bounded_android_import(module_id: str, title: str) -> dict:
    """Recover transient launcher/upgrade overlays; never tap unknown buttons.

    The same official pinned app can cold-start to a still-loading screen or
    show AOSP Pixel Launcher ANR. An absent button after one snapshot is not
    proof the import UI is unavailable; bounded retries must still fail closed.
    """
    initial = []
    recovery = []
    for index in range(6):
        observed = _screen(module_id, title)
        names = sorted({c["action"] for c in observed["controls"]})
        if index == 0:
            initial = names
        chosen = _tap(observed["controls"], (
            "LOAD DOCUMENTS FROM FILES", "LOAD DOCUMENT FROM FILES"
        ))
        if chosen is not None:
            return {
                "initial_buttons": initial,
                "recovery_actions": recovery,
                "import_button": chosen,
                "startup_snapshots_checked": index + 1,
            }
        fallback = _tap(observed["controls"], (
            "CLOSE APP", "WAIT", "DISMISS", "DISMISS UNTIL NEXT UPDATE", "ADVANCED"
        ))
        if fallback is not None:
            recovery.append(fallback)
        time.sleep(5)
    raise PilotError("Stable AndBible import UI not established after bounded recovery")


def _screenshot_sha256() -> str:
    data = adb("exec-out", "screencap", "-p", timeout=35)
    if not (2048 < len(data) < 5_000_000 and data.startswith(b"\x89PNG\r\n\x1a\n")):
        raise PilotError("Android real framebuffer unavailable")
    return sha256(data).hexdigest()


def _app_focus_witness() -> list[str]:
    """Record exact Android focus/lifecycle signal classes, never screen text.

    Android 35 may expose top activity through ActivityManager rather than
    WindowManager. Seeing the installed package somewhere in dumpsys is NOT
    evidence it is the current/resumed activity.
    """
    found = set()
    names = {
        b"mCurrentFocus": "focused_window",
        b"mFocusedApp": "focused_app_window",
        b"mResumedActivity": "resumed_activity",
        b"topResumedActivity": "top_resumed_activity",
        b"mTopResumedActivity": "top_resumed_activity",
    }
    for category, command in (("window", "windows"), ("activity", "activities")):
        output = adb("shell", "dumpsys", category, command, timeout=25, fail=False)
        if len(output) > 4_000_000:
            raise PilotError("Unbounded Android lifecycle metadata")
        for line in output.splitlines():
            if PACKAGE.encode("ascii") not in line:
                continue
            for prefix, label in names.items():
                if prefix in line:
                    found.add(label)
    return sorted(found)


def _app_foreground() -> bool:
    return bool(_app_focus_witness())


def _dispatch_documented_reference(manifest: dict) -> bool:
    """Only a recognized ActivityManager acceptance, not actual navigation."""
    response = adb(
        "shell", "am", "start", "-a", "android.intent.action.VIEW",
        "-d", _reference_uri(manifest), "-p", PACKAGE, timeout=30, fail=False
    )
    # adb(fail=False) returns empty bytes on command error. We must NOT
    # report a successful dispatch merely because it was invoked.
    return (b"Starting: Intent" in response or
            b"Warning: Activity not started" in response) and b"Error:" not in response


def _reference_uri(manifest: dict) -> str:
    first = manifest["sample_references"][0]
    match = re.fullmatch(r"([1-4]?[A-Za-z][A-Za-z ]{0,35}) ([1-9]\d{0,2}):([1-9]\d{0,2})", first)
    if not match:
        raise PilotError("Unreviewed original commentary Android reference probe")
    book, chapter, verse = match.groups()
    # Generated from an already pinned, reviewed manifest reference.
    ref = book.replace(" ", "") + "." + chapter + "." + verse
    return ("https://read.andbible.org/" + ref + "?" +
            urlencode({"document": manifest["module_id"], "v11n": "KJV"}))


def run_android_original(resource_id: str, *, apk: Path) -> dict:
    manifest = load_manifest(resource_id)
    module_id = manifest["module_id"]
    title = manifest["title"]
    if (not MODULE.fullmatch(module_id)
            or manifest["rights"]["status"] != "research_only"
            or manifest["rights"]["owner_approved"] is not False
            or apk.is_symlink() or not apk.is_file()
            or sha256(apk.read_bytes()).hexdigest() != APK_SHA256):
        raise PilotError("Original commentary / exact official AndBible APK not verified")
    for key in ("archive_sha256", "stock_conf_sha256"):
        if not isinstance(manifest.get(key), str) or not HEX.fullmatch(manifest[key]):
            raise PilotError("Both original stock fingerprints must be reviewed")
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix="commentary-android-private-original-") as tmp:
        root = Path(tmp)
        archive = root / "original-crosswire.zip"
        downloaded = fetch(manifest["sword_zip_url"], archive, manifest["provider"])
        if downloaded["sha256"] != manifest["archive_sha256"]:
            raise PilotError("Official CrossWire archive fingerprint drift")
        inspected = inspect_archive(
            archive, source_kind="sword", expected_module_id=module_id,
            expected_category="commentary",
        )
        conf = inspected["sword_conf"]
        if (conf["driver"] != "zCom" or conf["version"] != manifest["version"]
                or conf["language"] != manifest["language"]
                or (conf["versification"] or "KJV") != "KJV"):
            raise PilotError("Original stock zCom configuration identity drift")
        with ZipFile(archive) as zip_data:
            metadata = zip_data.read("mods.d/" + module_id.lower() + ".conf")
        confhash = sha256(metadata).hexdigest()
        if confhash != manifest["stock_conf_sha256"]:
            raise PilotError("Original SWORD commentary metadata changed")

        adb("wait-for-device", timeout=80)
        adb("install", "-r", str(apk), timeout=130)
        apps = adb("shell", "pm", "list", "packages", PACKAGE, timeout=20)
        if b"package:" + PACKAGE.encode("ascii") not in apps:
            raise PilotError("Official AndBible stable app missing after actual install")
        device_path = "/sdcard/Download/" + module_id + ".zip"
        adb("push", str(archive), device_path, timeout=110)
        adb("shell", "am", "broadcast", "-a",
            "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", "file://" + device_path, timeout=20, fail=False)

        adb("shell", "monkey", "-p", PACKAGE, "1", timeout=40)
        time.sleep(14)
        snapshots = {"startup": _screenshot_sha256()}
        history = []
        startup = _start_bounded_android_import(module_id, title)
        initial_buttons = startup["initial_buttons"]
        snap = _screen(module_id, title)
        proceeded = _tap(snap["controls"], ("PROCEED",)) is not None
        selected = False
        for step in range(7):
            snap = _screen(module_id, title)
            actions = sorted({c["action"] for c in snap["controls"]})
            history.append({"step": step, "safe_action_names": actions})
            chosen = _tap(snap["controls"], ("EXACT_MODULE_ZIP",))
            if chosen:
                selected = True
                time.sleep(16)
                break
            if not _tap(snap["controls"], ("DOWNLOADS", "DOWNLOAD", "BROWSE", "BROWSE FILES")):
                break
        if not selected:
            raise PilotError("Exact original stock ZIP was not selectable by Android file picker")
        snapshots["post_selection"] = _screenshot_sha256()
        selected_screen = _screen(module_id, title)
        exact_file_still_visible = any(
            item["action"] == "EXACT_MODULE_ZIP" for item in selected_screen["controls"]
        )
        focus_after_selection = _app_focus_witness()
        action_after = []
        for _step in range(3):
            snap = _screen(module_id, title)
            next_action = _tap(snap["controls"], ("IMPORT", "INSTALL", "OK", "CONTINUE", "DONE"))
            if next_action is None:
                break
            action_after.append(next_action)
            time.sleep(6)
        snap = _screen(module_id, title)
        identity_after_first_import = snap["reader_module_metadata_detected"]
        focus_after_import = _app_focus_witness()
        _tap(snap["controls"], ("DISMISS", "DISMISS UNTIL NEXT UPDATE"))
        time.sleep(2)
        snapshots["after_import_attempt"] = _screenshot_sha256()
        adb("shell", "am", "force-stop", PACKAGE, timeout=20)
        adb("shell", "monkey", "-p", PACKAGE, "1", timeout=40)
        time.sleep(12)
        after_restart = _screen(module_id, title)
        identity_after_restart = after_restart["reader_module_metadata_detected"]
        focus_after_restart = _app_focus_witness()
        # Real platform request result is checked, but not equated to a
        # rendered page. A rejected Intent must remain explicitly unverified.
        intent_accepted = _dispatch_documented_reference(manifest)
        time.sleep(7)
        after_link = _screen(module_id, title)
        identity_after_link = after_link["reader_module_metadata_detected"]
        focus_after_link = _app_focus_witness()
        snapshots["post_reference_dispatch"] = _screenshot_sha256()
        return {
            "schema_version": 1,
            "status": "pinned_original_zCom_stable_Android_ui_import_observation",
            "resource_id": resource_id,
            "sword_module_id": module_id,
            "andbible_apk_sha256": APK_SHA256,
            "crosswire_original_zip_sha256": downloaded["sha256"],
            "crosswire_original_conf_sha256": confhash,
            "official_android_application_installed": True,
            "official_android_app_file_import_action_tapped": True,
            "android_file_picker_exact_original_zip_selected": selected,
            "android_proceed_dialog_tapped": proceeded,
            "android_safe_import_confirmation_buttons_tapped": action_after,
            "original_module_metadata_detected_in_ui_after_import": (
                identity_after_first_import or identity_after_restart or identity_after_link
            ),
            "original_module_identity_witness_by_phase": {
                "after_import": identity_after_first_import,
                "after_app_restart": identity_after_restart,
                "after_reference_intent": identity_after_link,
            },
            "android_exact_file_row_still_visible_after_selection": exact_file_still_visible,
            "android_focus_witness_by_phase": {
                "after_file_selection": focus_after_selection,
                "after_import_attempt": focus_after_import,
                "after_app_restart": focus_after_restart,
                "after_reference_intent": focus_after_link,
            },
            "android_application_foreground_after_deeplink": bool(focus_after_link),
            "android_sample_reference_deeplink_attempted": True,
            "android_documented_intent_request_accepted": intent_accepted,
            "android_screen_changed_after_reference_attempt": (
                snapshots["post_reference_dispatch"] != snapshots["after_import_attempt"]
            ),
            "bounded_first_screen_available_actions": initial_buttons,
            "android_bounded_startup_recovery_actions": startup["recovery_actions"],
            "android_startup_snapshots_checked": startup["startup_snapshots_checked"],
            "bounded_file_picker_actions": history,
            "real_screen_sha256_only": snapshots,
            "original_text_and_reference_target_display_verified": False,
            "module_persistence_in_application_database_verified": False,
            "Android_commentary_links_verified": False,
            "Screenshots_or_commented_text_or_module_uploaded": False,
            "legal_editorial_release_approved": False,
            "published": False,
        }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--apk", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        raise PilotError("Refusing unsafe or existing Android report destination")
    result = run_android_original(args.resource_id, apk=args.apk)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Official stable Android app was tested with original pinned zCom; only safe UI metadata retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
