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
from urllib.parse import urlencode
import re
import subprocess
import struct
import time
import xml.etree.ElementTree as ET

from publisher_osis_preview_package import package_preview
from probe_andbible_android_emulator import APK_SHA256, PACKAGE, adb, capture_png, AndroidPreflightError

MODULE = "JND2024RepairResearch"
FINAL_RESEARCH_MODULE = "BRJND2024"
VERSIFICATION = "Luther"
DEVICE_ZIP = "/sdcard/Download/JND2024RepairResearch.zip"
SAFE_UI = frozenset({
    "LOAD DOCUMENTS FROM FILES", "LOAD DOCUMENT FROM FILES",
    "DOWNLOAD DOCUMENTS", "EASY START", "ADVANCED",
    "RECENT", "DOWNLOADS", "DOWNLOAD", "BROWSE FILES", "BROWSE",
    "JND2024REPAIRRESEARCH.ZIP", "BRJND2024.ZIP", "ALLOW", "WHILE USING THE APP",
    "INSTALL", "IMPORT", "OK", "OPEN", "CONTINUE", "DONE", "CLOSE",
    "USE THIS FOLDER", "GRANT ACCESS", "SELECT", "NEXT", "PROCEED",
    "DISMISS", "DISMISS UNTIL NEXT UPDATE", "WAIT", "CLOSE APP",
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
    # Only permit closing the *system launcher* when a matching exact
    # OS-level ANR title is present in this same bounded UI hierarchy.
    # Never expose a generic CLOSE APP button for AndBible itself.
    launcher_anr=any(
        node.attrib.get("text", "").strip().casefold() in {
            "pixel launcher isn't responding", "quickstep isn't responding"
        } for node in root.iter("node"))
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
            if (label in SAFE_UI and (label != "CLOSE APP" or launcher_anr)) or candidate_file:
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


DOCUMENTED_REFERENCE_PROBES = ("Gen.2.4", "Rom.16.25")
PARAGRAPH_LAYOUT_REFERENCE_PROBES = ("Gen.6.9", "Gen.6.13", "Gen.7.17", "Ps.3.1", "Job.3.1")
OMITTED_VERSE_NOTE_HOST_PROBES = ("Matt.23.13", "Acts.8.36", "Acts.15.33")


def open_documented_reference_probe(reference: str, *, module_id: str = MODULE) -> None:
    """Attempt only a pre-reviewed AndBible OSIS deep link in the pinned app.

    https://andbible.org/docs/bible_links/ documents /OSISREF with document,
    v11n. Intent invocation alone is NEVER proof of actual navigation.
    """
    if module_id not in {MODULE, FINAL_RESEARCH_MODULE}:
        raise AndroidDarbyImportError("Unreviewed SWORD module identity")
    if reference not in DOCUMENTED_REFERENCE_PROBES + OMITTED_VERSE_NOTE_HOST_PROBES + PARAGRAPH_LAYOUT_REFERENCE_PROBES:
        raise AndroidDarbyImportError("Unreviewed Android passage navigation")
    uri = ("https://read.andbible.org/" + reference + "?"
           + urlencode({"document": module_id, "v11n": VERSIFICATION}))
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW",
        "-d", uri, "-p", PACKAGE, timeout=25, fail=False)
    time.sleep(7)


def probe_observed_note_marker(screen: Path):
    """Research-only click on a manually verified original note glyph.

    The exact screenshot from Android run 43217039917, artifact 13944147727,
    12-documented-reference-attempt.png (SHA-256
    a191e1e7e5447701245c54fda902b4f01a1971342c16d88b22ea9ca443d5712e)
    displays the Rom.16.25 note 'b' at (823,1425) on 1080x2280 AOSP Pixel 4.
    This is a bounded *visual experiment*, not a generic coordinate rule,
    note text verification, or permission to publish.
    """
    data=screen.read_bytes()
    if (len(data) < 24 or data[:8] != bytes.fromhex("89504e470d0a1a0a")
            or struct.unpack(">II", data[16:24]) != (1080, 2280)):
        raise AndroidDarbyImportError("Unexpected AndBible reader screenshot geometry")
    adb("shell","input","tap","823","1425",timeout=12)
    time.sleep(4)


def probe_observed_corrected_colossians_link(screen: Path):
    """Research-only tap on source-repaired Col.2.2–3 hyperlink in real note.

    Actual run 43218512341 screenshot 13-romans-note-marker-probe.png
    SHA-256 7b8954b9d865dfaa4eee3b9ae58f70c2c722469696fd7b8c5de464e77604a688
    shows the blue '2.2-3' link at (840,1800), 1080x2280 Pixel 4.
    Actual navigation requires independent pixel examination; never infer
    successful corrected target selection from an ADB tap.
    """
    data=screen.read_bytes()
    if (len(data) < 24 or data[:8] != bytes.fromhex("89504e470d0a1a0a")
            or struct.unpack(">II", data[16:24]) != (1080, 2280)):
        raise AndroidDarbyImportError("Unexpected note popup screenshot geometry")
    adb("shell","input","tap","840","1800",timeout=12)
    time.sleep(5)


# Actual independent run 43220850024 screenshot samples, 1080x2280,
# with authorial note markers on the *host* verses, not omitted additions.
OMITTED_HOST_CALLER_SAMPLES = {
    "Matt.23.13": (225, 1217),  # original purple a, screenshot 15
    "Acts.8.36": (1017, 1080),  # original purple i, screenshot 16
    "Acts.15.33": (240, 1151),  # original purple e, screenshot 17
}


def probe_observed_omitted_host_caller(screen: Path, host: str) -> None:
    """Tap ONLY an independently observed test screenshot note caller."""
    if host not in OMITTED_HOST_CALLER_SAMPLES:
        raise AndroidDarbyImportError("Unknown omitted-verse note host")
    data=screen.read_bytes()
    if (len(data) < 24 or data[:8] != bytes.fromhex("89504e470d0a1a0a")
            or struct.unpack(">II", data[16:24]) != (1080, 2280)):
        raise AndroidDarbyImportError("Unexpected omitted-note reader geometry")
    x,y=OMITTED_HOST_CALLER_SAMPLES[host]
    adb("shell","input","tap",str(x),str(y),timeout=12)
    time.sleep(3)


# Real run 43223191886: underlined missing-verse labels remain blue after
# removal of machine osisRef targets. Determine their *actual* tap behavior.
# Exact 1080x2280 AOSP screenshots 15/16/17, independently reviewed.
OMITTED_NOTE_PRINTED_LINK_SAMPLES = {
    "Matt.23.13": (685, 1185),
    "Acts.8.36": (685, 1292),
    "Acts.15.33": (685, 1400),
}


def probe_observed_omitted_note_printed_link(screen: Path, host: str) -> None:
    """Research-only probe of blue omitted-verse reference, never a proof."""
    if host not in OMITTED_NOTE_PRINTED_LINK_SAMPLES:
        raise AndroidDarbyImportError("Unreviewed textual-critical note host")
    data=screen.read_bytes()
    if (len(data) < 24 or data[:8] != bytes.fromhex("89504e470d0a1a0a")
            or struct.unpack(">II", data[16:24]) != (1080, 2280)):
        raise AndroidDarbyImportError("Unexpected textual-critical popup geometry")
    x,y=OMITTED_NOTE_PRINTED_LINK_SAMPLES[host]
    adb("shell","input","tap",str(x),str(y),timeout=12)
    time.sleep(4)


def relaunch_for_persistence():
    """Restart the known official app without touching module files or reimporting."""
    adb("shell","am","force-stop",PACKAGE,timeout=20)
    adb("shell","monkey","-p",PACKAGE,"1",timeout=35)
    time.sleep(12)


def attempt_private_android_import(*, payload: Path, apk: Path,
                                   evidence_dir: Path, scratch: Path,
                                   module_id: str = MODULE) -> dict:
    if (not apk.is_file() or apk.is_symlink()
            or sha256(apk.read_bytes()).hexdigest() != APK_SHA256
            or evidence_dir.is_symlink() or not evidence_dir.is_dir()
            or any(evidence_dir.iterdir())
            or not scratch.is_dir() or scratch.is_symlink()
            or not ((module_id == MODULE and "private-darby-repaired-sword-" in str(payload.resolve()))
                    or (module_id == FINAL_RESEARCH_MODULE
                        and ({"darby-v011", "darby-private-native"} & set(payload.resolve().parts))
                        and payload.name == "payload"
                        and payload.parent.name == "final-module"
                        and payload.parent.parent.name in {"final-011-candidate", "private-final"}))):
        raise AndroidDarbyImportError("Unpinned APK or unsafe private experiment paths")

    if module_id not in {MODULE, FINAL_RESEARCH_MODULE}:
        raise AndroidDarbyImportError("Unexpected private final module identity")
    local_archive=scratch/"private-corrected-for-andbible-only.zip"
    receipt=package_preview(payload,local_archive,module_id,VERSIFICATION)
    device_zip = DEVICE_ZIP if module_id == MODULE else "/sdcard/Download/BRJND2024.zip"
    target_label = (module_id + ".zip").upper()
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
    adb("push",str(local_archive),device_zip,timeout=100)
    adb("shell","am","broadcast","-a",
        "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d","file://"+device_zip,timeout=18,fail=False)

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
    # Android emulator sometimes surfaces a Pixel Launcher ANR above an otherwise
    # ready AndBible first-run screen. Choose only its observed WAIT control;
    # never close a system process or blindly tap the obscured application.
    system_waits=0
    launcher_closed=False
    while (any(c["label"] in {"WAIT", "CLOSE APP"} for c in controls)
           and system_waits < 3):
        action=tap_allowlisted(controls,("CLOSE APP", "WAIT"))
        launcher_closed=launcher_closed or action == "CLOSE APP"
        system_waits+=1
        time.sleep(5)
        controls=android_controls()
    checkpoint("android_system_wait_recovery",attempts=system_waits,
               exact_launcher_anr_closed=launcher_closed,
               startup_controls_recovered=any(c["label"] == "LOAD DOCUMENTS FROM FILES" for c in controls))
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
                       candidate_visible=target_label in labels)
            item=tap_allowlisted(controls,(target_label,))
            if item:
                selected=True
                checkpoint("private_candidate_file_selected",selected=True)
                # Real SWORD import can briefly saturate the emulator; allow
                # the UI to settle before requesting a full framebuffer.
                time.sleep(16)
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
            for capture_attempt in range(2):
                try:
                    screenshots[f"{4+step:02d}-import-state"] = capture_png(
                        evidence_dir/f"{4+step:02d}-import-state.png")
                    break
                except AndroidPreflightError:
                    if capture_attempt:
                        raise
                    checkpoint("android_post_selection_capture_retry", index=step,
                               error_type="bounded_adb_screencap_failure")
                    time.sleep(12)
        except AndroidPreflightError:
            checkpoint("android_emulator_lost_during_import_attempt",
                       after_exact_file_selected=selected,
                       candidate_installation_not_verified=True)
            raise

    # The real exact-APK screenshot after selecting the ZIP (run 43195135975)
    # showed French John 3 under the research edition title, obscured by the
    # AndBible 5.1 post-install update dialog. Dismiss only this observed
    # optional announcement, and preserve unreviewed visual evidence.
    announcement_dismissed=False
    if selected:
        overlay_controls=android_controls()
        chosen_dismiss=tap_allowlisted(
            overlay_controls,("DISMISS", "DISMISS UNTIL NEXT UPDATE"))
        announcement_dismissed=chosen_dismiss is not None
        checkpoint("post_import_announcement",
                   dismiss_control_found=announcement_dismissed,
                   andbible_import_still_requires_independent_review=True)
        screenshots["08-after-optional-announcement"] = capture_png(
            evidence_dir/"08-after-optional-announcement.png")

    # Independently probe persistence across a real app process restart.
    # The module is NOT re-imported; this only records an observed reader
    # screenshot for subsequent human review, never automatic acceptance.
    relaunch_attempted=False
    if selected:
        relaunch_for_persistence()
        relaunch_attempted=True
        checkpoint("andbible_process_relaunch",attempted=True,
                   persistent_module_identity_verified=False,
                   rendered_notes_verified=False)
        screenshots["09-after-process-relaunch"] = capture_png(
            evidence_dir/"09-after-process-relaunch.png")
        # The stable APK may show its known upgrade dialog again on restart.
        # Dismiss the exact observed action only; do not infer app state from it.
        relaunch_controls=android_controls()
        relaunch_dismissed=tap_allowlisted(
            relaunch_controls,("DISMISS", "DISMISS UNTIL NEXT UPDATE"))
        checkpoint("relaunch_announcement",dismissed=relaunch_dismissed is not None,
                   persistent_module_identity_verified=False)
        screenshots["10-after-relaunch-dialog"] = capture_png(
            evidence_dir/"10-after-relaunch-dialog.png")
        # Native app-only URI handling is a RESEARCH probe. No forced URL
        # browser fallback or speculative passage/footnote tapping.
        for index, reference in enumerate(DOCUMENTED_REFERENCE_PROBES, start=11):
            open_documented_reference_probe(reference, module_id=module_id)
            checkpoint("android_documented_deep_link_attempt",
                       reference=reference, actual_target_verified=False,
                       note_popup_verified=False)
            key=f"{index:02d}-documented-reference-attempt"
            screenshots[key] = capture_png(evidence_dir/(key+".png"))
        # Only the last verified screen displays Rom 16:25, note caller b.
        # Trigger precisely that manually witnessed marker geometry and
        # independently inspect the resulting real UI; never auto-certify it.
        probe_observed_note_marker(evidence_dir/"12-documented-reference-attempt.png")
        checkpoint("romans_note_caller_visual_probe",
                   probe="observed_Rom.16.25_original_b",
                   note_popup_verified=False, repaired_link_click_verified=False)
        screenshots["13-romans-note-marker-probe"] = capture_png(
            evidence_dir/"13-romans-note-marker-probe.png")
        probe_observed_corrected_colossians_link(
            evidence_dir/"13-romans-note-marker-probe.png")
        checkpoint("romans_corrected_colossians_link_visual_probe",
                   popup_link="Col.2.2-Col.2.3", actual_navigation_verified=False)
        screenshots["14-corrected-colossians-link-probe"] = capture_png(
            evidence_dir/"14-corrected-colossians-link-probe.png")
        # Observe actual host verses for intentionally omitted textual-critical
        # additions. Do not navigate to those absent numbered verses and never
        # infer note popup fidelity from a reference intent alone.
        for index, reference in enumerate(OMITTED_VERSE_NOTE_HOST_PROBES, start=15):
            open_documented_reference_probe(reference, module_id=module_id)
            checkpoint("android_omitted_verse_note_host_probe",
                       host=reference, host_render_verified=False,
                       omitted_note_popup_verified=False)
            key=f"{index:02d}-omitted-verse-host"
            screenshots[key] = capture_png(evidence_dir/(key+".png"))
            probe_observed_omitted_host_caller(evidence_dir/(key+".png"), reference)
            checkpoint("android_omitted_verse_note_popup_visual_probe",
                       host=reference, note_popup_verified=False,
                       missing_verse_dead_link_verified=False)
            screenshots[key+"-note"] = capture_png(
                evidence_dir/(key+"-note.png"))
            probe_observed_omitted_note_printed_link(
                evidence_dir/(key+"-note.png"), reference)
            checkpoint("android_missing_verse_printed_link_tap",
                       host=reference, navigation_result_verified=False,
                       phantom_verse_absence_gui_verified=False)
            screenshots[key+"-reference-tap"] = capture_png(
                evidence_dir/(key+"-reference-tap.png"))
            adb("shell","input","keyevent","KEYCODE_BACK",timeout=12)
            time.sleep(2)
        # Post-import paragraph check uses only documented reference intents.
        # Capture the *actual repaired module* without trusting the intent to
        # establish navigation or visual correctness. Images require review.
        for idx, reference in enumerate(PARAGRAPH_LAYOUT_REFERENCE_PROBES, start=18):
            open_documented_reference_probe(reference, module_id=module_id)
            key=f"{idx:02d}-repaired-paragraph-{reference.replace('.', '-')}"
            screenshots[key] = capture_png(evidence_dir/(key+".png"))
            checkpoint("andbible_repaired_paragraph_visual_probe",
                       reference=reference, actual_module_and_reference_verified=False,
                       visible_editorial_stars_absent_verified=False,
                       leading_whitespace_accepted=False)

    # A successful ADB press does not establish a loaded translation; retain
    # that as a separate visual and Java/Android document validation gate.
    result={
        "schema_version":1,
        "status":"stable_andbible_android_private_zip_import_attempt_research_only",
        "andbible_release":"production-1117",
        "andbible_apk_sha256":APK_SHA256,
        "sword_module_id":module_id,
        "sword_versification":VERSIFICATION,
        "private_candidate_zip_sha256":receipt["zip_sha256"],
        "all_zip_files_identical_to_full_native_audit":True,
        "original_sword_xml_and_zip_uploaded":False,
        "first_screen_allowlisted_labels":first_labels,
        "import_button_found_and_pressed":chosen is not None,
        "import_instructions_proceeded": proceeded,
        "file_picker_candidate_selected":selected,
        "import_confirmation_action_attempted":import_prompt,
        "post_import_announcement_dismissed":announcement_dismissed,
        "andbible_process_relaunch_attempted":relaunch_attempted,
        "andbible_documented_reference_intent_attempted":relaunch_attempted,
        "andbible_documented_reference_navigation_verified":False,
        "andbible_romans_original_note_popup_verified":False,
        "andbible_colossians_note_link_gui_verified":False,
        "andbible_three_omitted_verse_host_gui_verified":False,
        "andbible_repaired_paragraph_gui_verified": False,
        "andbible_three_omitted_verse_note_popup_gui_verified":False,
        "andbible_missing_verse_click_behavior_verified":False,
        "andbible_persistent_module_identity_verified":False,
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
    if not (chosen and proceeded and selected):
        raise AndroidDarbyImportError(
            "Android UI import path incomplete: see safe-report.json and screenshots; "
            "the workflow must not report a green import attempt")
    print("Pinned AndBible Android private ZIP selected; GUI approval still pending")
    return result
