#!/usr/bin/env python3
"""Test-only Xiphos GTK startup with a SHA-pinned isolated SWORD module.

This is a headless GUI *startup* diagnostic only: process liveness and optional
X11 window registration do not certify rendered text, note-click navigation,
typography, comparison or owner publication approval. No screenshot or
Scripture/notes/log excerpts are published.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from zipfile import ZipFile

MODULE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,48}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
V11N = re.compile(r"[A-Za-z][A-Za-z0-9]{1,31}\Z")
PARTS = ("ot", "nt")
EXTS = ("bzs", "bzv", "bzz")


class XiphosSmokeError(ValueError):
    """Unsafe module preview or headless Xiphos startup did not pass."""


def extract_pinned_preview(archive: Path, root: Path, module: str,
                           expected_sha: str,versification:str) -> Path:
    """Accept only the standard seven-file zText layout; never unsafe ZIP paths."""
    if (not MODULE.fullmatch(module) or not HEX.fullmatch(expected_sha)
            or not V11N.fullmatch(versification)
            or archive.is_symlink() or not archive.is_file()
            or not root.is_dir()):
        raise XiphosSmokeError("Untrusted preview identity or output location")
    data=archive.read_bytes()
    if sha256(data).hexdigest()!=expected_sha:
        raise XiphosSmokeError("Module preview SHA-256 mismatch")
    slug=module.lower()
    expected={f"mods.d/{slug}.conf"}
    expected|={f"modules/texts/ztext/{slug}/{part}.{ext}"
               for part in PARTS for ext in EXTS}
    with ZipFile(archive) as z:
        members=z.infolist()
        if (len(members)!=len(expected) or {x.filename for x in members}!=expected
                or z.testzip() is not None):
            raise XiphosSmokeError("Unexpected SWORD ZIP contents")
        for info in members:
            mode=(info.external_attr>>16)&0o170000
            if info.is_dir() or mode not in {0,0o100000} or info.file_size>40_000_000:
                raise XiphosSmokeError("Nonregular or unsafe SWORD member")
            target=root/info.filename
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(info))
    conf=(root/"mods.d"/f"{slug}.conf").read_text(encoding="utf-8")
    if (not conf.startswith(f"[{module}]\n")
            or f"DataPath=./modules/texts/ztext/{slug}/\n" not in conf
            or "ModDrv=zText\n" not in conf
            or f"Versification={versification}\n" not in conf):
        raise XiphosSmokeError("SWORD preview conf identity or versification mismatch")
    return root


def _stop_group(proc):
    if proc.poll() is None:
        try:
            os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait(timeout=5)


def _visible_window(env):
    for search in (["xdotool","search","--onlyvisible","--class","[Xx]iphos"],
                   ["xdotool","search","--onlyvisible","--name","[Xx]iphos"]):
        try:
            result=subprocess.run(search,env=env,stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL,timeout=4,check=False)
        except (OSError,subprocess.TimeoutExpired):
            return False
        if result.returncode==0 and result.stdout.strip():
            return True
    return False


def smoke(archive:Path,module:str,expected_sha:str,versification:str,startup_seconds:int,
          screenshot:Path|None=None):
    if not isinstance(startup_seconds,int) or not 5<=startup_seconds<=25:
        raise XiphosSmokeError("Unbounded headless startup duration")
    with tempfile.TemporaryDirectory(prefix="isolated-xiphos-preview-") as temp:
        base=Path(temp)
        payload_root=base/"payload"
        payload_root.mkdir()
        payload=extract_pinned_preview(archive,payload_root,module,expected_sha,versification)
        # Separate HOME prevents global user preferences from influencing the trial.
        home=base/"home"
        home.mkdir()
        env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(home/"config"),
                 XDG_CACHE_HOME=str(home/"cache"),SWORD_PATH=str(payload),
                 DISPLAY=":91",GDK_BACKEND="x11",NO_AT_BRIDGE="1")
        xvfb=None
        app=None
        try:
            xvfb=subprocess.Popen(["Xvfb",":91","-screen","0","1280x800x24",
                                   "-nolisten","tcp"],stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL,start_new_session=True)
            time.sleep(1.5)
            if xvfb.poll() is not None:
                raise XiphosSmokeError("Virtual X11 display failed to initialize")
            app=subprocess.Popen(["dbus-run-session","--","xiphos"],env=env,
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                 start_new_session=True)
            end=time.monotonic()+startup_seconds
            while time.monotonic()<end:
                if app.poll() is not None:
                    raise XiphosSmokeError("Xiphos terminated before bounded startup gate")
                time.sleep(0.5)
            window=_visible_window(env)
            screenshot_sha=None
            if screenshot is not None:
                if not window:
                    raise XiphosSmokeError("Cannot review screenshot without visible Xiphos window")
                # Dismiss possible first-run locale notice without editing application
                # preferences or relying on window geometry.
                subprocess.run(["xdotool","key","--clearmodifiers","Return"],
                               env=env,stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,timeout=4,check=False)
                time.sleep(1.5)
                if (screenshot.is_symlink() or screenshot.exists()
                        or not screenshot.parent.is_dir()
                        or screenshot.suffix.lower()!=".png"):
                    raise XiphosSmokeError("Refusing unsafe screenshot destination")
                try:
                    snap=subprocess.run(["import","-display",env["DISPLAY"],
                                         "-window","root",str(screenshot)],
                                        env=env,stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,timeout=15,
                                        check=False)
                except (OSError,subprocess.TimeoutExpired) as exc:
                    raise XiphosSmokeError("X11 screenshot capture failed") from exc
                if snap.returncode!=0 or screenshot.stat().st_size>6_000_000:
                    raise XiphosSmokeError("Invalid bounded screenshot result")
                screenshot_sha=sha256(screenshot.read_bytes()).hexdigest()
            return {
                "status":"headless_xiphos_running_after_bounded_startup",
                "reader":"xiphos",
                "startup_seconds":startup_seconds,
                "sha256_verified":True,
                "isolated_standard_ztext_package":True,
                "x11_window_detected_not_visually_inspected":window,
                "test_only_screenshot_sha256":screenshot_sha,
                "screenshot_external_review_required":screenshot is not None,
                "actual_rendered_text_fidelity_verified":False,
                "actual_note_click_navigation_verified":False,
                "parallel_reading_verified":False,
                "visual_typography_or_owner_signoff":False,
                "published":False,
            }
        finally:
            if app is not None:
                _stop_group(app)
            if xvfb is not None:
                _stop_group(xvfb)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip",type=Path,required=True)
    parser.add_argument("--module-id",required=True)
    parser.add_argument("--sha256",required=True)
    parser.add_argument("--versification",required=True)
    parser.add_argument("--seconds",type=int,default=12)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--screenshot",type=Path)
    args=parser.parse_args()
    if args.report.exists() or not args.report.parent.is_dir():
        parser.error("Refuse overwrite or missing report parent")
    receipt=smoke(args.zip,args.module_id,args.sha256,args.versification,args.seconds,
                  screenshot=args.screenshot)
    args.report.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Xiphos test-only capture classified; no screenshot pixels or Bible text logged")


if __name__=="__main__":
    main()
