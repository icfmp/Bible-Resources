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
import shutil
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



def install_checked_out_rawtext_comparison(
    source: Path, root: Path, module: str, versification: str,
) -> dict:
    """Install a *separate*, checked-out standard RawText module for reader review.

    Only five expected SWORD files are accepted. The existing reviewed module
    is copied without changing bytes or source metadata; never download a
    floating second edition or confuse two installed modules with visual
    parallel-reading approval.
    """
    if (not MODULE.fullmatch(module) or not V11N.fullmatch(versification)
            or source.is_symlink() or not source.is_dir()
            or root.is_symlink() or not root.is_dir()):
        raise XiphosSmokeError("Untrusted comparison source or module identity")
    slug = module.lower()
    conf_rel = f"mods.d/{slug}.conf"
    data_rel = f"modules/texts/rawtext/{slug}"
    expected = {conf_rel} | {
        f"{data_rel}/{part}{ext}"
        for part in PARTS for ext in ("", ".vss")
    }
    observed = set()
    for entry in source.rglob("*"):
        if entry.is_symlink() or (not entry.is_file() and not entry.is_dir()):
            raise XiphosSmokeError("Unsafe comparison module member")
        if entry.is_file():
            observed.add(entry.relative_to(source).as_posix())
    if observed != expected:
        raise XiphosSmokeError("Unexpected comparison RawText file set")
    conf_path = source / conf_rel
    if conf_path.stat().st_size > 16_000:
        raise XiphosSmokeError("Comparison module configuration too large")
    conf = conf_path.read_text(encoding="utf-8")
    if (not conf.startswith(f"[{module}]\n")
            or f"DataPath=./{data_rel}/\n" not in conf
            or "ModDrv=RawText\n" not in conf
            or f"Versification={versification}\n" not in conf):
        raise XiphosSmokeError("Comparison identity, driver or v11n mismatch")
    # Check every file before copying anything to avoid an invalid partial
    # comparison installation. Never overwrite the independently pinned Bible.
    for rel in sorted(expected):
        original = source / rel
        target = root / rel
        if (not original.is_file() or original.is_symlink()
                or not 0 < original.stat().st_size <= 40_000_000
                or target.exists() or target.is_symlink()):
            raise XiphosSmokeError("Unsafe or colliding comparison SWORD file")
    for rel in sorted(expected):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, target)
    return {
        "module_id": module,
        "driver": "RawText",
        "versification": versification,
        "file_count": len(expected),
        "copied_from_existing_reviewed_checkout": True,
        "gui_two_module_parallel_content_verified": False,
    }


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



def _notice_click_from_geometry(geometry: dict[str, int]) -> tuple[int,int] | None:
    """Locate the center-bottom button of a small transient notice window.

    Avoid clicking the normal Bible-reading window or an unknown dialog.
    Coordinates are computed for this fixed virtual-display harness only.
    """
    x,y,w,h=(geometry.get(k) for k in ("X","Y","WIDTH","HEIGHT"))
    if not all(isinstance(v,int) for v in (x,y,w,h)):
        return None
    if x<0 or y<0 or w<220 or w>820 or h<80 or h>240:
        return None
    return x+w//2,y+h-18


def _dismiss_transient_xiphos_notice(env):
    """Best-effort modal dismissal. No click if small Xiphos window absent."""
    try:
        found=subprocess.run(["xdotool","search","--onlyvisible","--name",
                              "^[Xx]iphos$"],env=env,stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL,timeout=4,check=False)
    except (OSError,subprocess.TimeoutExpired):
        return False
    if found.returncode:
        return False
    for item in found.stdout.decode("ascii",errors="ignore").splitlines():
        if not item.isdecimal():
            continue
        try:
            dims=subprocess.run(["xdotool","getwindowgeometry","--shell",item],
                                env=env,stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL,timeout=4,check=False)
        except (OSError,subprocess.TimeoutExpired):
            continue
        if dims.returncode:
            continue
        values={}
        for line in dims.stdout.decode("ascii",errors="ignore").splitlines():
            if "=" not in line:
                continue
            key,value=line.split("=",1)
            if key in {"X","Y","WIDTH","HEIGHT"} and value.isdecimal():
                values[key]=int(value)
        point=_notice_click_from_geometry(values)
        if point is None:
            continue
        try:
            clicked=subprocess.run(["xdotool","mousemove","--sync",
                                    str(point[0]),str(point[1]),"click","1"],
                                   env=env,stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,timeout=4,check=False)
        except (OSError,subprocess.TimeoutExpired):
            return False
        return clicked.returncode==0
    return False


# Representative universal navigation examples; no authored verse data edits.
READER_SAMPLES = (
    ("genesis-prose", "Gen 1:1"),
    ("psalm-poetry", "Ps 23:1"),
    ("matthew-heading", "Matt 5:1"),
    ("romans-annotation", "Rom 8:28"),
)


# Verified Xvfb screenshot geometry from read-only stage-6 run #43072470491:
# after focusing/resizing the 1216x736 window, an authored superscript
# note caller is visible at Gen.1.2 near (503,520). This coordinate is ONLY
# an ephemeral reader-UI interaction specimen, not a translation mapping.
GENESIS_1_2_NOTE_HOVER = (503, 520)


def _capture_note_hover_sample(env:dict, out:Path) -> dict:
    """Move over one visibly identified note caller, capture possible preview.

    Xiphos footnotes use mouse hover; this only observes pixels for manual
    inspection and never pretends the hover actually resolved the note body.
    """
    if (env.get("DISPLAY") != ":91" or not out.is_dir()
            or out.is_symlink()):
        raise XiphosSmokeError("Unreviewed footnote hover display or directory")
    target=out/"genesis-note-hover.png"
    if target.exists() or target.is_symlink():
        raise XiphosSmokeError("Refusing existing note-hover screenshot")
    x,y=GENESIS_1_2_NOTE_HOVER
    try:
        moved=subprocess.run(
            ["xdotool","mousemove","--sync",str(x),str(y)],
            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=5,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise XiphosSmokeError("Bounded original-note hover unavailable") from exc
    if moved.returncode:
        raise XiphosSmokeError("Original note hover pointer movement failed")
    time.sleep(1.5)
    try:
        captured=subprocess.run(
            ["import","-display",env["DISPLAY"],"-window","root",str(target)],
            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=15,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise XiphosSmokeError("Original note hover screenshot failed") from exc
    if (captured.returncode or not target.is_file() or target.is_symlink()
            or not 0 < target.stat().st_size <= 6_000_000):
        raise XiphosSmokeError("Unsafe original-note hover screenshot")
    # Return cursor to neutral screen area before navigating a new passage.
    try:
        subprocess.run(
            ["xdotool","mousemove","1200","740"],
            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=4,check=False)
    except (OSError,subprocess.TimeoutExpired):
        pass
    return {
        "host_reference": "Gen.1.2",
        "interaction": "pointer_hover_over_visible_note_caller",
        "screenshot_sha256": sha256(target.read_bytes()).hexdigest(),
        "previewed_note_body_verified": False,
        "actual_link_navigation_verified": False,
        "visual_review_required": True,
        "text_or_note_content_exported_to_metadata": False,
    }


def _sample_reader_passages(env, out: Path) -> list[dict]:
    """Xiphos Ctrl+L navigation with actual screenshots, not content approval."""
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        raise XiphosSmokeError("Unsafe sample screenshot output directory")
    # No screen coordinates: Ctrl+L is a documented Xiphos shortcut.
    # Confirm that a visible normal Xiphos window is the keyboard recipient.
    try:
        found = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "[Xx]iphos"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise XiphosSmokeError("Xiphos normal window not discoverable") from exc
    if found.returncode:
        raise XiphosSmokeError("Cannot focus real Xiphos reading window")
    candidates = [item for item in found.stdout.decode(
        "ascii", errors="ignore").splitlines() if item.isdecimal()]
    if not candidates:
        raise XiphosSmokeError("No valid Xiphos window ID for study sample")
    try:
        focus = subprocess.run(
            # No EWMH window manager runs inside this isolated Xvfb display.
            # windowactivate requires _NET_ACTIVE_WINDOW; direct X11 focus
            # works without mutating any user desktop or global preferences.
            ["xdotool", "windowfocus", "--sync", candidates[-1]],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise XiphosSmokeError("Cannot activate Xiphos study window") from exc
    if focus.returncode:
        raise XiphosSmokeError("Xiphos study window focus failed")
    # In bare Xvfb, the default Xiphos window occupies only ~800x600 pixels,
    # leaving a narrow center reader where Genesis headings hide verse 1.
    # Resize the actual test-only X11 window; never alter any user desktop.
    for command in (
        ["xdotool", "windowsize", candidates[-1], "1216", "736"],
        ["xdotool", "windowmove", candidates[-1], "16", "16"],
    ):
        try:
            adjusted=subprocess.run(
                command, env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise XiphosSmokeError("Bounded X11 study window resizing unavailable") from exc
        if adjusted.returncode:
            raise XiphosSmokeError("X11 study reader resizing failed")
    time.sleep(0.5)
    out.mkdir(mode=0o700)
    snapshots = []
    for slug, ref in READER_SAMPLES:
        for command in (
            ["xdotool", "key", "--clearmodifiers", "ctrl+l"],
            ["xdotool", "type", "--clearmodifiers", "--delay", "35", ref],
            ["xdotool", "key", "Return"],
        ):
            try:
                completed = subprocess.run(
                    command, env=env, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=10, check=False)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise XiphosSmokeError("Bounded X11 reader navigation unavailable") from exc
            if completed.returncode:
                raise XiphosSmokeError("X11 reader keyboard navigation failed")
        time.sleep(2)
        target = out / (slug + ".png")
        try:
            capture = subprocess.run(
                ["import", "-display", env["DISPLAY"], "-window", "root",
                 str(target)], env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise XiphosSmokeError("Bounded reader navigation screenshot failed") from exc
        if (capture.returncode or not target.is_file()
                or target.is_symlink() or target.stat().st_size > 6_000_000):
            raise XiphosSmokeError("Unsafe or failed virtual reader screenshot")
        snapshot={
            "sample": slug,
            "requested_reference": ref,
            "screenshot_sha256": sha256(target.read_bytes()).hexdigest(),
            "gui_navigation_outcome_requires_visual_inspection": True,
        }
        if slug == "genesis-prose":
            snapshot["note_hover_sample"] = _capture_note_hover_sample(env, out)
        snapshots.append(snapshot)
    return snapshots



def _capture_module_tree_probe(env: dict, study_dir: Path) -> dict:
    """Probe a second Bible selection in the isolated Xiphos module tree.

    Four bounded screenshots expose the GTK tree, second-module opening and
    a real passage-navigation attempt. Pixel content requires independent
    review; an executed pointer command is never selection proof.
    """
    if (env.get("DISPLAY") != ":91" or not study_dir.is_dir()
            or study_dir.is_symlink()):
        raise XiphosSmokeError("Unsafe dual-module Xiphos tree probe")
    pictures = []
    commands = (
        ["xdotool", "mousemove", "--sync", "100", "134", "click", "1"],
        ["xdotool", "key", "Right"],
        ["xdotool", "mousemove", "--sync", "100", "202", "click", "1"],
        ["xdotool", "key", "Right"],
        ["xdotool", "mousemove", "--sync", "120", "247"],
        ["xdotool", "click", "--repeat", "2", "--delay", "160", "1"],
        ["xdotool", "key", "--clearmodifiers", "ctrl+l"],
        ["xdotool", "type", "--clearmodifiers", "--delay", "35", "Gen 1:1"],
        ["xdotool", "key", "Return"],
    )
    for i, command in enumerate(commands):
        try:
            result = subprocess.run(
                command, env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise XiphosSmokeError("Bounded module-tree action unavailable") from exc
        if result.returncode:
            raise XiphosSmokeError("Module-tree interaction failed")
        if i not in (1, 3, 5, 8):
            continue
        target = study_dir / ("module-tree-stage-" + str(i) + ".png")
        if target.exists() or target.is_symlink():
            raise XiphosSmokeError("Refusing to overwrite module-tree evidence")
        time.sleep(0.5)
        try:
            captured = subprocess.run(
                ["import", "-display", env["DISPLAY"], "-window", "root",
                 str(target)], env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise XiphosSmokeError("Module-tree screenshot unavailable") from exc
        if (captured.returncode or not target.is_file()
                or not 0 < target.stat().st_size <= 6_000_000):
            raise XiphosSmokeError("Unsafe module-tree screenshot")
        pictures.append({
            "step": i,
            "screenshot_sha256": sha256(target.read_bytes()).hexdigest(),
            "module_selection_verified": False,
        })
    return {
        "inspection_only": True,
        "snapshots": pictures,
        "attempted_second_tree_module_open_and_genesis_navigation": True,
        "module_selection_verified": False,
    }


def _capture_parallel_toggle_sample(env:dict, study_dir:Path) -> dict:
    """Exercise Xiphos Alt-P and capture screenshot, never infer actual comparison."""
    if (not study_dir.is_dir() or study_dir.is_symlink()
            or not study_dir.parent.is_dir()
            or env.get("DISPLAY") != ":91"):
        raise XiphosSmokeError("Unsafe parallel screenshot fixture")
    target=study_dir/"parallel-toggle.png"
    if target.exists() or target.is_symlink():
        raise XiphosSmokeError("Refusing to overwrite parallel screenshot")
    try:
        toggled=subprocess.run(
            ["xdotool","key","--clearmodifiers","alt+p"],
            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=5,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise XiphosSmokeError("Parallel keyboard probe unavailable") from exc
    if toggled.returncode:
        raise XiphosSmokeError("Parallel keyboard probe failed")
    time.sleep(1.5)
    try:
        snap=subprocess.run(
            ["import","-display",env["DISPLAY"],"-window","root",str(target)],
            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=15,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise XiphosSmokeError("Parallel screenshot capture unavailable") from exc
    if (snap.returncode or not target.is_file() or target.is_symlink()
            or not 0 < target.stat().st_size <= 6_000_000):
        raise XiphosSmokeError("Unsafe parallel screenshot capture")
    return {
        "shortcut_invoked": "Alt+P",
        "screenshot_sha256": sha256(target.read_bytes()).hexdigest(),
        "actual_parallel_second_translation_visible_verified": False,
        "gui_outcome_requires_visual_inspection": True,
        # Xiphos may update its own temporary HOME preferences; do not
        # claim that GUI configuration is unchanged.
        "original_pinned_preview_zip_modified": False,
    }


def smoke(archive:Path,module:str,expected_sha:str,versification:str,startup_seconds:int,
          screenshot:Path|None=None, study_dir:Path|None=None,
          comparison_root:Path|None=None, comparison_module:str="",
          comparison_versification:str=""):
    if not isinstance(startup_seconds,int) or not 5<=startup_seconds<=25:
        raise XiphosSmokeError("Unbounded headless startup duration")
    with tempfile.TemporaryDirectory(prefix="isolated-xiphos-preview-") as temp:
        base=Path(temp)
        payload_root=base/"payload"
        payload_root.mkdir()
        payload=extract_pinned_preview(archive,payload_root,module,expected_sha,versification)
        comparison = None
        if comparison_root is not None:
            comparison = install_checked_out_rawtext_comparison(
                comparison_root, payload_root, comparison_module,
                comparison_versification)
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
                notice_dismissed=_dismiss_transient_xiphos_notice(env)
                fixed_viewport_fallback_attempted=False
                if not notice_dismissed and env.get("DISPLAY")==":91":
                    # Fixed 1280x800 Xvfb test screen: first-start Xiphos
                    # locale warning observed at (0,0)-(564,135). Click only
                    # its broad bottom-center OK strip. This ephemeral test
                    # session has a private HOME; never use on user desktop.
                    fixed_viewport_fallback_attempted=True
                    try:
                        click=subprocess.run(
                            ["xdotool","mousemove","--sync","282","116","click","1"],
                            env=env,stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,timeout=4,check=False)
                        notice_dismissed=click.returncode==0
                    except (OSError,subprocess.TimeoutExpired):
                        notice_dismissed=False
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
            samples = _sample_reader_passages(env, study_dir) if study_dir else []
            tree_probe = (_capture_module_tree_probe(env, study_dir)
                          if comparison and study_dir and samples else None)
            parallel_attempt = (_capture_parallel_toggle_sample(env, study_dir)
                                if study_dir and samples else None)
            return {
                "status":"headless_xiphos_running_after_bounded_startup",
                "reader":"xiphos",
                "startup_seconds":startup_seconds,
                "sha256_verified":True,
                "isolated_standard_ztext_package":True,
                "x11_window_detected_not_visually_inspected":window,
                "test_only_screenshot_sha256":screenshot_sha,
                "real_reader_passage_samples":samples,
                "parallel_view_toggle_sample":parallel_attempt,
                "independent_comparison_module":comparison,
                "module_selection_probe":tree_probe,
                "keyboard_navigation_attempted": bool(samples),
                "isolated_virtual_display_notice_click_fallback_attempted":(
                    fixed_viewport_fallback_attempted if screenshot is not None else False),
                "transient_small_notice_dismissal_attempt_succeeded":(
                    notice_dismissed if screenshot is not None else False),
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
    parser.add_argument("--study-dir",type=Path)
    parser.add_argument("--comparison-root",type=Path)
    parser.add_argument("--comparison-module-id",default="")
    parser.add_argument("--comparison-versification",default="")
    args=parser.parse_args()
    if args.report.exists() or not args.report.parent.is_dir():
        parser.error("Refuse overwrite or missing report parent")
    receipt=smoke(args.zip,args.module_id,args.sha256,args.versification,args.seconds,
                  screenshot=args.screenshot, study_dir=args.study_dir,
                  comparison_root=args.comparison_root,
                  comparison_module=args.comparison_module_id,
                  comparison_versification=args.comparison_versification)
    args.report.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Xiphos test-only capture classified; no screenshot pixels or Bible text logged")


if __name__=="__main__":
    main()
