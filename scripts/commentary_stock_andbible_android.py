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
from zipfile import ZipFile, ZIP_DEFLATED

from commentary_xiphos_dual_reader import (
    BIBLE_MODULE, verify_and_install_reviewed_bible,
)

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
    baseline_label = BIBLE_MODULE.upper() + ".ZIP"
    # AndBible stable's MainBibleActivity uses commentaryButton with
    # resource-id '<package>:id/commentaryButton' (main_bible_view.xml).
    # Its popup item text is "<book abbreviation> (language)" (menuForDocs).
    # Exact MHCC (en), never MHC (en), identifies the concise edition.
    commentary_toolbar_resource = PACKAGE + ":id/commentaryButton"
    exact_commentary_popup = module_id.upper() + " (EN)"
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
        for key, value in zip(("text", "content-desc"), candidates):
            # Source metadata identity only, not user-authored or rendered prose.
            if value.strip().casefold() in (module_id.casefold(), title.casefold()):
                module_label_in_tree = True
            label = value.strip().upper()
            has_commentary_toolbar_id = (
                key == "content-desc" and
                node.attrib.get("resource-id") == commentary_toolbar_resource
            )
            exact_popup_entry = (label == exact_commentary_popup)
            first_download_finish = (
                node.attrib.get("resource-id") == PACKAGE + ":id/okayButton"
                and node.attrib.get("enabled") == "true"
                and node.attrib.get("clickable") == "true"
            )
            if (label not in SAFE and label not in (file_label, baseline_label)
                    and not has_commentary_toolbar_id and not exact_popup_entry
                    and not first_download_finish):
                continue
            if label == "CLOSE APP" and not launcher_anr:
                continue
            match = BOUNDS.fullmatch(node.attrib.get("bounds", ""))
            if not match:
                continue
            x1, y1, x2, y2 = map(int, match.groups())
            if not (0 <= x1 < x2 <= 1600 and 0 <= y1 < y2 <= 2400):
                continue
            action = ("FINISH_FIRST_DOWNLOAD" if first_download_finish
                      else "OPEN_COMMENTARY_MENU" if has_commentary_toolbar_id
                      else "EXACT_COMMENTARY_MENU_MODULE" if exact_popup_entry
                      else "EXACT_MODULE_ZIP" if label == file_label
                      else "EXACT_REVIEWED_BIBLE_ZIP" if label == baseline_label
                      else label)
            item = {"action": action,
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
        if choice not in SAFE and choice not in {
            "EXACT_MODULE_ZIP", "EXACT_REVIEWED_BIBLE_ZIP",
            "FINISH_FIRST_DOWNLOAD",
            "OPEN_COMMENTARY_MENU", "EXACT_COMMENTARY_MENU_MODULE"
        }:
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


def _attempt_commentary_toolbar_selection(module_id: str, title: str) -> dict:
    """Use the reader toolbar's actual resource-id to select EXACT MHCC (en).

    A different edition labeled MHC (en) MUST NOT satisfy the selection.
    AndBible menuForDocs can auto-switch with two documents instead of
    showing a menu; a switch alone remains unverified without visible
    source-module identity. No hard-coded tap coordinates or source prose.
    """
    if not MODULE.fullmatch(module_id):
        raise PilotError("Unreviewed commentary toolbar identity")
    before = _screen(module_id, title)
    opened = _tap(before["controls"], ("OPEN_COMMENTARY_MENU",))
    if not opened:
        return {
            "actual_commentary_toolbar_resource_found": False,
            "exact_original_commentary_popup_item_found": False,
            "exact_original_commentary_menu_item_tapped": False,
            "reader_source_identity_witness_after_selection": False,
            "reader_screen_changed_after_selection": False,
            "possible_auto_switch_without_menu": False,
        }
    before_sha = _screenshot_sha256()
    opened_screen = _screen(module_id, title)
    items = opened_screen["controls"]
    exact_found = any(x["action"] == "EXACT_COMMENTARY_MENU_MODULE" for x in items)
    clicked = _tap(items, ("EXACT_COMMENTARY_MENU_MODULE",)) if exact_found else None
    after = _screen(module_id, title)
    after_sha = _screenshot_sha256()
    return {
        "actual_commentary_toolbar_resource_found": True,
        "exact_original_commentary_popup_item_found": exact_found,
        "exact_original_commentary_menu_item_tapped": clicked is not None,
        "reader_source_identity_witness_after_selection": (
            after["reader_module_metadata_detected"]
        ),
        "reader_screen_changed_after_selection": before_sha != after_sha,
        "possible_auto_switch_without_menu": (
            not exact_found and after["reader_module_metadata_detected"]
        ),
    }


def _screenshot_sha256() -> str:
    data = adb("exec-out", "screencap", "-p", timeout=35)
    if not (2048 < len(data) < 5_000_000 and data.startswith(b"\x89PNG\r\n\x1a\n")):
        raise PilotError("Android real framebuffer unavailable")
    return sha256(data).hexdigest()


# Only these exact resource identifiers from AndBible production-1117
# main_bible_view.xml may be disclosed as diagnostic flags.
KNOWN_READER_VIEW_IDS = frozenset({
    "bibleButton", "commentaryButton", "workspaceButton",
    "optionsMenu", "strongsButton", "searchButton", "speakButton",
})


def _classify_main_reader_context(xml: bytes, activity_dump: bytes) -> dict:
    """Diagnose UI context without exporting any source prose or UI strings.

    An Android test can have imported a SWORD ZIP yet still be on a welcome,
    permission, document download or chooser screen. In that case a missing
    commentary toolbar is not evidence of incompatible commentary content.
    """
    if (not isinstance(xml, bytes) or not isinstance(activity_dump, bytes)
            or len(xml) > 3_000_000 or len(activity_dump) > 4_000_000):
        raise PilotError("Unbounded Android layout/activity diagnostic")
    ids = set()
    try:
        tree = ET.fromstring(xml) if xml else None
    except ET.ParseError:
        tree = None
    if tree is not None:
        for node in tree.iter("node"):
            rid = node.attrib.get("resource-id", "")
            prefix = PACKAGE + ":id/"
            if rid.startswith(prefix):
                name = rid[len(prefix):]
                if name in KNOWN_READER_VIEW_IDS:
                    ids.add(name)
    resumed_lines = [
        ln for ln in activity_dump.splitlines()
        if any(name in ln for name in (
            b"topResumedActivity", b"mResumedActivity", b"mTopResumedActivity",
        ))
    ]
    reader = any(b"MainBibleActivity" in ln and PACKAGE.encode() in ln
                 for ln in resumed_lines)
    other_andbible = any(PACKAGE.encode() in ln for ln in resumed_lines)
    return {
        "known_reader_toolbar_resource_ids_visible": sorted(ids),
        "main_bible_reader_activity_resumed": reader,
        "another_andbible_activity_resumed": other_andbible and not reader,
        "ui_hierarchy_has_any_elements": tree is not None,
        "actual_commentary_rendering_verified": False,
    }


def _reader_context_witness() -> dict:
    adb("shell", "uiautomator", "dump", "/sdcard/commentary-context-ui.xml",
        timeout=40, fail=False)
    xml = adb("exec-out", "cat", "/sdcard/commentary-context-ui.xml",
              timeout=20, fail=False)
    activity = adb("shell", "dumpsys", "activity", "activities",
                   timeout=30, fail=False)
    return _classify_main_reader_context(xml, activity)


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


def _create_attested_reviewed_bible_zip(directory: Path) -> Path:
    """Package only the five unchanged, independently attested published Bible files.

    No recompilation, relabeling, scripture rewriting or global SWORD install.
    The exact previously approved BRLSG1910 file hashes are checked before
    packaging and again after opening the disposable archive.
    """
    if directory.is_symlink() or not directory.is_dir():
        raise PilotError("Unsafe private reviewed Bible packaging directory")
    installed = directory / "attested-bible"
    installed.mkdir()
    witness = verify_and_install_reviewed_bible(installed)
    if (witness["module_id"] != BIBLE_MODULE or
            witness["all_five_published_bible_files_sha256_attested"] is not True):
        raise PilotError("No approved baseline Bible source attestation")
    members = (
        "mods.d/brlsg1910.conf",
        "modules/texts/rawtext/brlsg1910/ot",
        "modules/texts/rawtext/brlsg1910/ot.vss",
        "modules/texts/rawtext/brlsg1910/nt",
        "modules/texts/rawtext/brlsg1910/nt.vss",
    )
    output = directory / (BIBLE_MODULE + ".zip")
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as target:
        for relative in members:
            candidate = installed / relative
            if candidate.is_symlink() or not candidate.is_file():
                raise PilotError("Missing exact attested Bible SWORD member")
            target.write(candidate, arcname=relative)
    with ZipFile(output, "r") as review:
        if set(review.namelist()) != set(members):
            raise PilotError("Baseline Bible ZIP member list changed")
        for relative in members:
            if review.read(relative) != (installed / relative).read_bytes():
                raise PilotError("Baseline Bible ZIP changed approved payload bytes")
    return output


def _select_exact_download_zip(
    module_id: str, title: str, *, wanted: str, max_steps: int = 7,
) -> tuple[bool, list[dict]]:
    """Use only an actually observed exact-basename Android file-picker row."""
    if wanted not in {"EXACT_REVIEWED_BIBLE_ZIP", "EXACT_MODULE_ZIP"}:
        raise PilotError("Unreviewed Android file picker module choice")
    history = []
    for step in range(max_steps):
        snap = _screen(module_id, title)
        actions = sorted({c["action"] for c in snap["controls"]})
        history.append({"step": step, "safe_action_names": actions})
        if _tap(snap["controls"], (wanted,)) is not None:
            time.sleep(16)
            return True, history
        if not _tap(
            snap["controls"], ("DOWNLOADS", "DOWNLOAD", "BROWSE", "BROWSE FILES")
        ):
            break
    return False, history


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
        reviewed_bible_zip = _create_attested_reviewed_bible_zip(root)
        adb("push", str(reviewed_bible_zip),
            "/sdcard/Download/" + BIBLE_MODULE + ".zip", timeout=110)
        # The original MHCC file-picker probe explicitly informs MediaStore.
        # The second ZIP needs its *own* scan; otherwise Android DocumentsUI
        # may not expose the approved Bible despite a successful adb push.
        adb("shell", "am", "broadcast", "-a",
            "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", "file:///sdcard/Download/" + BIBLE_MODULE + ".zip",
            timeout=20, fail=False)
        time.sleep(3)
        adb("shell", "am", "broadcast", "-a",
            "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", "file://" + device_path, timeout=20, fail=False)

        adb("shell", "monkey", "-p", PACKAGE, "1", timeout=40)
        time.sleep(14)
        snapshots = {"startup": _screenshot_sha256()}
        history = []
        startup = _start_bounded_android_import(module_id, title)
        initial_buttons = startup["initial_buttons"]
        # InstallZip.getFileFromUserAndInstall() opens a separate, real
        # "Proceed" confirmation *before* ACTION_OPEN_DOCUMENT. This is not
        # the FirstDownload Okay button, which requires an installed Bible.
        dialog = _screen(module_id, title)
        proceeded = _tap(dialog["controls"], ("PROCEED",)) is not None
        if not proceeded:
            raise PilotError("Exact official InstallZip file-picker Proceed was not observed")
        bible_selected, baseline_history = _select_exact_download_zip(
            module_id, title, wanted="EXACT_REVIEWED_BIBLE_ZIP",
        )
        if not bible_selected:
            observed = sorted({
                name for step in baseline_history for name in step["safe_action_names"]
            })
            raise PilotError(
                "Reviewed baseline Bible ZIP was not selectable in Android file picker; "
                "allowlisted actual action classes: " + ",".join(observed)
            )
        baseline_before_proceed = _reader_context_witness()
        # Stay in the first-download flow to import the original MHCC next.
        # The registered Bible must subsequently enable FirstDownload's
        # *different* actual okayButton before entering MainBibleActivity.
        startup_commentary = _start_bounded_android_import(module_id, title)
        dialog = _screen(module_id, title)
        commentary_dialog_proceeded = _tap(dialog["controls"], ("PROCEED",)) is not None
        if not commentary_dialog_proceeded:
            raise PilotError("Second original commentary InstallZip Proceed not observed")
        selected, history = _select_exact_download_zip(
            module_id, title, wanted="EXACT_MODULE_ZIP",
        )
        if not selected:
            raise PilotError("Exact original stock ZIP was not selectable by Android file picker")
        # This is the first-download completion *after* both ZIPs, not an
        # arbitrary "OK" dialog. Refuse to tap a disabled or spoofed control.
        post_both = _screen(module_id, title)
        first_download_completed = _tap(
            post_both["controls"], ("FINISH_FIRST_DOWNLOAD",)
        ) is not None
        time.sleep(3)
        baseline_after_proceed = _reader_context_witness()
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
        reader_context_after_restart = _reader_context_witness()
        # Follow the user-observed commentary books icon in the real reader
        # toolbar; this tests selection instead of guessing a deep link.
        toolbar_probe = _attempt_commentary_toolbar_selection(module_id, title)
        reader_context_after_toolbar = _reader_context_witness()
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
            "reviewed_bible_module_id": BIBLE_MODULE,
            "reviewed_bible_all_five_published_files_attested": True,
            "reviewed_bible_zip_selected_in_actual_file_picker": bible_selected,
            "original_commentary_installzip_proceed_tapped": commentary_dialog_proceeded,
            "first_download_enabled_okay_button_tapped": first_download_completed,
            "android_reviewed_bible_baseline_reader_before_proceed": baseline_before_proceed,
            "android_reviewed_bible_baseline_reader_after_proceed": baseline_after_proceed,
            "android_baseline_bible_picker_actions": baseline_history,
            "android_startup_commentary_snapshots_checked": startup_commentary["startup_snapshots_checked"],
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
            "android_commentary_toolbar_selection": toolbar_probe,
            "android_reader_context_by_phase": {
                "after_app_restart": reader_context_after_restart,
                "after_commentary_toolbar_attempt": reader_context_after_toolbar,
            },
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
