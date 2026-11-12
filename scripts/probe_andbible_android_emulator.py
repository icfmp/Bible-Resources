#!/usr/bin/env python3
"""Read-only stable AndBible 5.1.1117 Android emulator import-UI reconnaissance.

Installs an exactly pinned, official release APK into a disposable emulator.
Screenshots and sanitized UI-control labels only: no SWORD module is imported
or published. This preflight is NOT a Darby Android compatibility acceptance.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

APK_SHA256 = "1c9ed93391642c0de4529065a65e10eb44242d60722231b917b14c5919cdf796"
PACKAGE = "net.bible.android.activity"
ALLOWED_UI_LABELS = {
    "Advanced", "Easy", "Welcome", "Get started", "Get Started", "Continue",
    "Skip", "Proceed", "OK", "Download documents", "Download Documents",
    "Load Documents From Files", "Load Document From Files",
    "Load documents from files", "Load document from files",
    "Load from files", "Choose document", "Choose Document",
}


class AndroidPreflightError(ValueError):
    pass


def adb(*args: str, timeout: int = 40, fail: bool = True) -> bytes:
    try:
        result = subprocess.run(["adb", *args], stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AndroidPreflightError("Bounded ADB interaction failed") from exc
    if result.returncode and fail:
        raise AndroidPreflightError("ADB command returned nonzero")
    if len(result.stdout) > 5 * 1024 * 1024:
        raise AndroidPreflightError("Excessive Android automation output")
    return result.stdout if result.returncode == 0 else b""


def capture_png(out: Path):
    if out.exists() or out.is_symlink():
        raise AndroidPreflightError("Refusing existing or symlink screenshot")
    image = adb("exec-out", "screencap", "-p", timeout=30)
    if not image.startswith(b"\x89PNG\r\n\x1a\n") or not 2048 < len(image) < 5_000_000:
        raise AndroidPreflightError("Real Android screenshot was not acquired")
    out.write_bytes(image)
    return sha256(image).hexdigest()


def ui_controls():
    adb("shell", "uiautomator", "dump", "/sdcard/andbible-preflight-ui.xml",
        timeout=35, fail=False)
    content = adb("exec-out", "cat", "/sdcard/andbible-preflight-ui.xml",
                  timeout=15, fail=False)
    if not content or len(content) > 3_000_000:
        return []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []
    control = []
    for node in root.iter("node"):
        labels = (node.attrib.get("text", ""), node.attrib.get("content-desc", ""))
        for label in labels:
            if label in ALLOWED_UI_LABELS:
                bounds = node.attrib.get("bounds", "")
                m = re.fullmatch(r"\[(\d{1,4}),(\d{1,4})\]\[(\d{1,4}),(\d{1,4})\]", bounds)
                if m:
                    x1,y1,x2,y2 = map(int,m.groups())
                    if 0 <= x1 < x2 <= 1600 and 0 <= y1 < y2 <= 2400:
                        control.append({"label": label, "x": (x1+x2)//2,
                                        "y": (y1+y2)//2})
    return control[:40]


def pick(control, names):
    for label in names:
        for c in control:
            if c["label"] == label:
                adb("shell", "input", "tap", str(c["x"]), str(c["y"]))
                time.sleep(2)
                return label
    return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    args=p.parse_args()
    if (not args.apk.is_file() or args.apk.is_symlink()
            or sha256(args.apk.read_bytes()).hexdigest() != APK_SHA256
            or args.evidence.is_symlink() or
            not args.evidence.is_dir() or any(args.evidence.iterdir())):
        p.error("Official release APK pin or clean evidence directory failed")
    adb("wait-for-device",timeout=80)
    adb("install", "-r", str(args.apk),timeout=120)
    installed=adb("shell","pm","list","packages",PACKAGE,timeout=18).decode("ascii",errors="ignore")
    if "package:"+PACKAGE not in installed:
        raise AndroidPreflightError("Official AndBible package did not install")
    adb("shell","monkey","-p",PACKAGE,"1",timeout=35)
    time.sleep(14)
    first=capture_png(args.evidence/"stable-andbible-startup.png")
    controls1=ui_controls()
    tapped=pick(controls1,("Advanced",))
    controls2=ui_controls() if tapped else controls1
    selected=pick(controls2,(
        "Load Documents From Files","Load documents from files",
        "Load Document From Files","Load document from files",
        "Load from files",
    ))
    after=capture_png(args.evidence/"stable-andbible-import-screen.png")
    output={
        "schema_version":1,
        "status":"official_stable_andbible_android_emulator_ui_preflight_only",
        "source_release":"AndBible production-1117",
        "installed_android_package":PACKAGE,
        "apk_sha256":APK_SHA256,
        "startup_screenshot_sha256":first,
        "import_screen_screenshot_sha256":after,
        "bounded_control_labels_on_first_screen":sorted(set(x["label"] for x in controls1)),
        "bounded_control_labels_after_advanced":sorted(set(x["label"] for x in controls2)),
        "advanced_tapped":tapped is not None,
        "file_import_action_tapped":selected is not None,
        "imported_darby_or_any_private_bible":False,
        "android_bible_text_or_links_checked":False,
        "private_module_created_or_released":False,
        "independent_pixel_review_required":True,
    }
    (args.evidence/"report.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",
                                             encoding="utf-8")
    print("AndBible stable Android launched; sanitized UI metadata-only preflight completed")


if __name__=="__main__":
    main()
