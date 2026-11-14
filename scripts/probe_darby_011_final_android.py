#!/usr/bin/env python3
"""Actual stable AndBible Android UI probe on the exact PRIVATE Darby 0.1.1 ZIP.

Only a SHA-locked, previously full-source-audited BRJND2024 0.1.1 candidate
is accepted. Reuses the existing allowlisted Android file-picker controls.
The reviewed ZIP bytes are copied unchanged under a fixed *picker alias*;
their internal SWORD identity stays BRJND2024, version 0.1.1. Captures are
evidence, NEVER automatic proof of correct GUI rendering or publication.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import time
from urllib.parse import urlencode
from zipfile import ZipFile

from probe_andbible_android_private_import import (
    adb, android_controls, tap_allowlisted, capture_png, APK_SHA256, PACKAGE,
)

VERSION = "0.1.1"
MODULE = "BRJND2024"
V11N = "Luther"
RESEARCH_PICKER_ALIAS = "JND2024RepairResearch.zip"
DEVICE = "/sdcard/Download/" + RESEARCH_PICKER_ALIAS
VERSES = ("Gen.6.9", "Gen.6.13", "Gen.7.17", "Ps.3.1", "Job.3.1")
HEX = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED = {"mods.d/brjnd2024.conf"} | {
    "modules/texts/ztext/brjnd2024/" + side + "." + ext
    for side in ("ot", "nt") for ext in ("bzs", "bzv", "bzz")
}


class FinalDarbyAndroidError(ValueError):
    pass


def verify_final_candidate(archive: Path, metadata: dict) -> dict:
    """Check the exact archived candidate, not merely the test alias filename."""
    if not archive.is_file() or archive.is_symlink() or archive.name != "BRJND2024-0.1.1.zip":
        raise FinalDarbyAndroidError("Missing exact private final-ID archive")
    if metadata.get("status") != "reproducible_private_final_module_id_0_1_1_preflight_verified":
        raise FinalDarbyAndroidError("Private final-ID full audit missing")
    checksum = metadata.get("private_final_candidate_sword_zip_sha256")
    if not isinstance(checksum, str) or not HEX.fullmatch(checksum):
        raise FinalDarbyAndroidError("Untrusted candidate digest")
    if checksum != sha256(archive.read_bytes()).hexdigest():
        raise FinalDarbyAndroidError("Final candidate changed after SWORD native proof")
    if (metadata.get("independently_inspected_final_module_id") != MODULE or
        metadata.get("final_conf_version") != VERSION or
        metadata.get("native_verse_index_verified") is not True or
        metadata.get("source_verse_keys") != 31166 or
        metadata.get("source_note_count") != 6340 or
        metadata.get("all_521_division_metadata_source_native_pairs_verified") is not True or
        metadata.get("binary_data_unchanged_during_identity_promotion") is not True or
        metadata.get("owner_release_approval") is not False or
        metadata.get("published") is not False):
        raise FinalDarbyAndroidError("Incomplete final source/native provenance")
    with ZipFile(archive) as z:
        if set(z.namelist()) != EXPECTED or len(z.namelist()) != 7 or z.testzip() is not None:
            raise FinalDarbyAndroidError("Unexpected final-ID ZIP members")
        conf = z.read("mods.d/brjnd2024.conf").decode("utf-8")
        if not (conf.startswith("[BRJND2024]\n") and
                "\nVersion=0.1.1\n" in ("\n" + conf + "\n") and
                "\nModDrv=zText\n" in ("\n" + conf + "\n") and
                "\nVersification=Luther\n" in ("\n" + conf + "\n")):
            raise FinalDarbyAndroidError("Not the final SWORD module edition")
        member_hashes = metadata.get("six_ztext_member_hashes", {})
        if (not isinstance(member_hashes, dict) or len(member_hashes) != 6):
            raise FinalDarbyAndroidError("No original native member digests")
        for name in EXPECTED - {"mods.d/brjnd2024.conf"}:
            # The promotion report tracks exactly six unchanged SWORD members.
            source_name = name.replace("brjnd2024/", "jnd2024repairresearch/")
            available = (name, source_name, Path(name).name)
            expected_hash = next((member_hashes[x] for x in available if x in member_hashes), None)
            if expected_hash is None or sha256(z.read(name)).hexdigest() != expected_hash:
                raise FinalDarbyAndroidError("Final binary SWORD member not byte-attested")
    return {"zip_sha256": checksum, "zip_member_count": 7,
            "module_id": MODULE, "version": VERSION, "versification": V11N,
            "checked_sword_member_hashes": 6, "not_published": True}


def probe(archive: Path, meta_path: Path, apk: Path, evidence_dir: Path,
          report_path: Path) -> dict:
    if (not meta_path.is_file() or meta_path.is_symlink() or
        not apk.is_file() or apk.is_symlink() or
        sha256(apk.read_bytes()).hexdigest() != APK_SHA256 or
        evidence_dir.is_symlink() or not evidence_dir.is_dir() or
        any(evidence_dir.iterdir()) or report_path.exists() or
        report_path.is_symlink() or report_path.parent != evidence_dir):
        raise FinalDarbyAndroidError("Unsafe private Android preflight paths")
    attestation = verify_final_candidate(archive, json.loads(meta_path.read_text()))
    alias = evidence_dir.parent / RESEARCH_PICKER_ALIAS
    if alias.exists() or alias.is_symlink():
        raise FinalDarbyAndroidError("Refusing to overwrite a picker alias")
    shutil.copyfile(archive, alias)
    if sha256(alias.read_bytes()).hexdigest() != attestation["zip_sha256"]:
        raise FinalDarbyAndroidError("Picker alias is not byte-identical to final ZIP")
    adb("wait-for-device", timeout=80)
    adb("install", "-r", str(apk), timeout=120)
    packages = adb("shell", "pm", "list", "packages", PACKAGE,
                   timeout=18).decode("ascii", errors="ignore")
    if "package:" + PACKAGE not in packages:
        raise FinalDarbyAndroidError("Official stable AndBible APK did not install")
    adb("push", str(alias), DEVICE, timeout=100)
    adb("shell", "am", "broadcast", "-a",
        "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", "file://" + DEVICE, timeout=18, fail=False)
    adb("shell", "monkey", "-p", PACKAGE, "1", timeout=35)
    time.sleep(14)
    imgs = {}
    def capture(slug):
        path = evidence_dir / (slug + ".png")
        capture_png(path)
        imgs[slug] = sha256(path.read_bytes()).hexdigest()

    capture("01-startup")
    controls = android_controls()
    for _ in range(3):
        if not any(c["label"] in {"WAIT", "CLOSE APP"} for c in controls):
            break
        tap_allowlisted(controls, ("CLOSE APP", "WAIT"))
        time.sleep(5)
        controls = android_controls()
    load = tap_allowlisted(controls, ("LOAD DOCUMENTS FROM FILES",
                                        "LOAD DOCUMENT FROM FILES"))
    proceeded = False
    selected = False
    installed_attempt = False
    if load:
        capture("02-open-import")
        proceeded = tap_allowlisted(android_controls(), ("PROCEED",)) is not None
    if proceeded:
        capture("03-picker")
        visited_downloads = False
        for attempt in range(5):
            controls = android_controls()
            labels = {c["label"] for c in controls}
            if not selected:
                if "JND2024REPAIRRESEARCH.ZIP" in labels:
                    selected = tap_allowlisted(controls,
                                               ("JND2024REPAIRRESEARCH.ZIP",)) is not None
                    time.sleep(12)
                elif not visited_downloads:
                    visited_downloads = tap_allowlisted(controls,
                                    ("DOWNLOADS", "DOWNLOAD")) is not None
                else:
                    break
            else:
                pressed = tap_allowlisted(controls,
                             ("INSTALL", "IMPORT", "OK", "OPEN", "CONTINUE", "DONE"))
                installed_attempt = installed_attempt or pressed is not None
                if pressed is None:
                    break
                time.sleep(4)
            capture(f"0{4+attempt}-picker-state")
    if not (load and proceeded and selected):
        raise FinalDarbyAndroidError("Final 0.1.1 ZIP was not selected by the actual Android picker")

    controls = android_controls()
    tap_allowlisted(controls, ("DISMISS", "DISMISS UNTIL NEXT UPDATE"))
    capture("10-post-import-screen")
    # Launch requested exact original references in the FINAL-ID module. An
    # Android VIEW intent does not on its own prove document navigation.
    for i, ref in enumerate(VERSES, start=11):
        uri = ("https://read.andbible.org/" + ref + "?" +
               urlencode({"document": MODULE, "v11n": V11N}))
        adb("shell", "am", "start", "-a", "android.intent.action.VIEW",
            "-d", uri, "-p", PACKAGE, timeout=25, fail=False)
        time.sleep(7)
        capture(f"{i:02d}-final-{ref.replace('.', '-')}")
    if sha256(archive.read_bytes()).hexdigest() != attestation["zip_sha256"]:
        raise FinalDarbyAndroidError("Private final ZIP changed after Android trial")
    result = {
        "schema_version": 1,
        "status": "private_final_011_real_android_gui_capture_needs_independent_visual_review",
        "exact_final_internal_module_id": MODULE,
        "exact_final_internal_version": VERSION,
        "final_zip_sha256": attestation["zip_sha256"],
        "picker_alias_is_byte_identical_to_final_zip": True,
        "stable_andbible_apk_sha256": APK_SHA256,
        "picker_loaded_document_button_found": bool(load),
        "picker_proceeded": proceeded, "actual_final_candidate_row_selected": selected,
        "install_confirmation_attempted": installed_attempt,
        "final_bible_gui_reference_intents_requested": list(VERSES),
        "app_module_identity_observed_in_pixels": False,
        "all_requested_references_visually_verified": False,
        "final_011_visible_stars_absent_verified": False,
        "final_011_paragraph_indentation_accepted": False,
        "screenshots_sha256": imgs,
        "independent_screenshot_inspection_required": True,
        "original_source_zip_uploaded": False,
        "public_release_published": False,
    }
    report_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("Captured stable AndBible on exact SHA-pinned final-ID 0.1.1 module; visual approval pending")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--final-zip", required=True, type=Path)
    p.add_argument("--metadata", required=True, type=Path)
    p.add_argument("--apk", required=True, type=Path)
    p.add_argument("--evidence-dir", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    a = p.parse_args()
    probe(a.final_zip, a.metadata, a.apk, a.evidence_dir, a.report)


if __name__ == "__main__":
    main()
