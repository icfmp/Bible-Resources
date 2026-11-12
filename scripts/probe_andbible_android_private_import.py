#!/usr/bin/env python3
"""Attempt native stable AndBible 5.1.1117 Android import of exact audited SWORD ZIP.

Executed exclusively on a disposable, privately booted emulator. The app
and candidate are pinned. Only UI element identities and screenshots leave
the runner. Button press != successful import, and import != reader approval.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

from publisher_osis_preview_package import package_preview
from probe_andbible_android_emulator import APK_SHA256, PACKAGE, adb, capture_png, AndroidPreflightError

MODULE = "JND2024RepairResearch"
VERSIFICATION = "Luther"
DEVICE_ZIP = "/sdcard/Download/JND2024RepairResearch.zip"
SAFE_UI = frozenset({
    "LOAD DOCUMENTS FROM FILES", "LOAD DOCUMENT FROM FILES",
    "DOWNLOAD DOCUMENTS", "EASY START", "ADVANCED",
    "RECENT", "DOWNLOADS", "DOWNLOAD", "BROWSE FILES", "BROWSE",
    "JND2024REPAIRRESEARCH.ZIP", "ALLOW", "WHILE USING THE APP",
    "INSTALL", "IMPORT", "OK", "OPEN", "CONTINUE", "DONE", "CLOSE",
    "USE THIS FOLDER", "GRANT ACCESS", "SELECT", "NEXT", "PROCEED",
})


class AndroidDarbyImportError(ValueError):
    """Unsafe Android interaction or unverified immutable test input."""


def safe_controls(xml: bytes) -> list[dict]:
    """Find fixed allowlisted controls, not arbitrary screen text."""
    if not isinstance(xml, bytes) or len(xml) > 3_000_000:
        raise AndroidDarbyImportError("Unbounded Android UI tree")
    try:
        root=ET.fromstring(xml)
    except ET.ParseError:
        return []
    result=[]
    for node in root.iter("node"):
        bounds=node.attrib.get("bounds","")
        match=re.fullmatch(r"\[(\d{1,4}),(\d{1,4})\]\[(\d{1,4}),(\d{1,4})\]",bounds)
        if not match:
            continue
        x1,y1,x2,y2=map(int,match.groups())
        if not 0<=x1<x2<=1600 or not 0<=y1<y2<=2400:
            continue
        for key in ("text","content-desc"):
            value=node.attrib.get(key,"").strip()
            label=value.upper()
            candidate_file=(value.startswith("JND2024Repai") and len(value)<=48
                            and re.fullmatch(r"JND2024Repai[A-Za-z0-9 ._…-]*",value) is not None)
            if label in SAFE_UI or candidate_file:
                item={"label":("JND2024REPAIRRESEARCH.ZIP" if candidate_file else label),
                      "x":(x1+x2)//2,"y":(y1+y2)//2}
                if item not in result:
                    result.append(item)
    return result[:50]


def android_controls():
    adb("shell","uiautomator","dump","/sdcard/andbible-private-import-ui.xml",
        timeout=40,fail=False)
    xml=adb("exec-out","cat","/sdcard/andbible-private-import-ui.xml",
            timeout=20,fail=False)
    return safe_controls(xml) if xml else []


def tap_allowlisted(controls, ordered_labels):
    for label in ordered_labels:
        if label not in SAFE_UI:
            raise AndroidDarbyImportError("Disallowed UI action")
        for c in controls:
            if c["label"] == label:
                adb("shell","input","tap",str(c["x"]),str(c["y"]),timeout=12)
                time.sleep(3)
                return label
    return None


def attempt_private_android_import(*, payload: Path, apk: Path,
                                   evidence_dir: Path, scratch: Path) -> dict:
    if (not apk.is_file() or apk.is_symlink()
            or sha256(apk.read_bytes()).hexdigest() != APK_SHA256
            or evidence_dir.is_symlink() or not evidence_dir.is_dir()
            or any(evidence_dir.iterdir())
            or not scratch.is_dir() or scratch.is_symlink()
            or not "private-darby-repaired-sword-" in str(payload.resolve())):
        raise AndroidDarbyImportError("Unpinned APK or unsafe private experiment paths")

    local_archive=scratch/"private-corrected-for-andbible-only.zip"
    receipt=package_preview(payload,local_archive,MODULE,VERSIFICATION)
    if (not receipt["all_module_files_byte_identical_to_audited_candidate"]
            or receipt["preview_only"] is not True
            or receipt["release_approved"] is not False):
        raise AndroidDarbyImportError("SWORD candidate is not the audited research-only input")

    adb("wait-for-device",timeout=80)
    adb("install","-r",str(apk),timeout=120)
    apps=adb("shell","pm","list","packages",PACKAGE,timeout=18).decode("ascii",errors="ignore")
    if "package:"+PACKAGE not in apps:
        raise AndroidDarbyImportError("Official AndBible APK did not install")

    # ADB push keeps the private module inside this disposable emulator; no
    # public cloud artifact or ordinary Android filesystem is written.
    adb("push",str(local_archive),DEVICE_ZIP,timeout=100)
    adb("shell","am","broadcast","-a",
        "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d","file://"+DEVICE_ZIP,timeout=18,fail=False)

    adb("shell","monkey","-p",PACKAGE,"1",timeout=35)
    time.sleep(14)
    trace=[]
    def checkpoint(phase, **fields):
        item={"phase":phase,**fields}
        trace.append(item)
        (evidence_dir/"progress.json").write_text(
            json.dumps({"schema_version":1,
                        "status":"research_only_android_ui_attempt_no_approval",
                        "trace":trace,
                        "android_gui_import_confirmed":False},
                       indent=2,sort_keys=True)+"\n",encoding="utf-8")
    checkpoint("private_zip_pushed_and_official_apk_started")
    screenshots={}
    screenshots["01-startup"]=capture_png(evidence_dir/"01-andbible-startup.png")

    controls=android_controls()
    first_labels=sorted({c["label"] for c in controls})
    checkpoint("official_initial_startup_ui",safe_control_labels=first_labels)
    chosen=tap_allowlisted(controls,("LOAD DOCUMENTS FROM FILES",
                                     "LOAD DOCUMENT FROM FILES"))
    proceeded=False
    checkpoint("andbible_load_document_button",found=chosen is not None)
    if chosen is not None:
        screenshots["02-import-instructions"]=capture_png(
            evidence_dir/"02-import-instructions.png")
        instructions=android_controls()
        proceeded=tap_allowlisted(instructions,("PROCEED",)) is not None
        checkpoint("andbible_import_proceed_dialog",pressed=proceeded)
        if proceeded:
            time.sleep(2)
            screenshots["03-android-file-picker"]=capture_png(
                evidence_dir/"03-android-file-picker.png")
    history=[]
    selected=False
    import_prompt=False
    imported_by_app=False
    visited_downloads=False
    for step in range(4) if proceeded else range(0):
        controls=android_controls()
        labels=sorted({c["label"] for c in controls})
        history.append(labels)
        checkpoint("android_picker_state",index=step,allowed_labels=labels)
        if not selected:
            checkpoint("try_exact_private_candidate_file",
                       candidate_visible="JND2024REPAIRRESEARCH.ZIP" in labels)
            item=tap_allowlisted(controls,("JND2024REPAIRRESEARCH.ZIP",))
            if item:
                selected=True
                checkpoint("private_candidate_file_selected",selected=True)
                time.sleep(5)
            elif not visited_downloads:
                folder=tap_allowlisted(controls,("DOWNLOADS","DOWNLOAD"))
                if folder:
                    visited_downloads=True
                else:
                    break
            else:
                break
        else:
            item=tap_allowlisted(controls,("INSTALL","IMPORT","OK","OPEN",
                                           "CONTINUE","DONE"))
            if item:
                import_prompt=True
                time.sleep(4)
            else:
                break
        try:
            screenshots[f"{4+step:02d}-import-state"] = capture_png(
                evidence_dir/f"{4+step:02d}-import-state.png")
        except AndroidPreflightError:
            checkpoint("android_emulator_lost_during_import_attempt",
                       after_exact_file_selected=selected,
                       candidate_installation_not_verified=True)
            raise

    # A successful ADB press does not establish a loaded translation; retain
    # that as a separate visual and Java/Android document validation gate.
    result={
        "schema_version":1,
        "status":"stable_andbible_android_private_zip_import_attempt_research_only",
        "andbible_release":"production-1117",
        "andbible_apk_sha256":APK_SHA256,
        "sword_module_id":MODULE,
        "sword_versification":VERSIFICATION,
        "private_candidate_zip_sha256":receipt["zip_sha256"],
        "all_zip_files_identical_to_full_native_audit":True,
        "original_sword_xml_and_zip_uploaded":False,
        "first_screen_allowlisted_labels":first_labels,
        "import_button_found_and_pressed":chosen is not None,
        "import_instructions_proceeded": proceeded,
        "file_picker_candidate_selected":selected,
        "import_confirmation_action_attempted":import_prompt,
        "andbible_import_verified":imported_by_app,
        "andbible_rendered_text_and_notes_verified":False,
        "andbible_repaired_reference_gui_click_verified":False,
        "screen_state_safe_control_labels":history,
        "screenshots_sha256":screenshots,
        "independent_screenshot_review_required":True,
        "published_or_editorially_approved":False,
    }
    (evidence_dir/"safe-report.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Pinned AndBible Android candidate import UI attempted; no publication/visual claims")
    return result
