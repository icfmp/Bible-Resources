#!/usr/bin/env python3
"""Private actual Xiphos GTK startup against an exact SHA-pinned stock zCom.

This is ONLY a first independent GUI startup gate. A visible X11 window does
not establish that an authorial passage, reference link or note was rendered
correctly; manual Xiphos and AndBible passage/navigation checks remain open.
Never export screenshot pixels or original commentary contents in CI.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from zipfile import ZipFile

from commentary_intake import load_manifest
from commentary_native_raw_inventory import _safe_stock_install
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from pilot_subprocess import present_key, query
from reader_xiphos_headless_smoke import _stop_group, _visible_window


def _probe_real_gui(root: Path, *, seconds: int) -> dict:
    """Start Xiphos in a disposable HOME and Xvfb, never on the user's display."""
    if (type(seconds) is not int or not 6 <= seconds <= 25
            or root.is_symlink() or not root.is_dir()
            or not (root / "mods.d").is_dir()):
        raise PilotError("Unsafe independent GUI startup context")
    for exe in ("Xvfb", "dbus-run-session", "xiphos", "xdotool"):
        if shutil.which(exe) is None:
            raise PilotError("Required installed Xiphos GUI smoke tool is missing")
    private_home = root.parent / "private-gui-home"
    if private_home.exists() or private_home.is_symlink():
        raise PilotError("GUI test home already exists")
    private_home.mkdir(mode=0o700)
    for d in ("config", "cache", "data"):
        (private_home / d).mkdir()
    env = dict(
        os.environ,
        HOME=str(private_home),
        XDG_CONFIG_HOME=str(private_home / "config"),
        XDG_CACHE_HOME=str(private_home / "cache"),
        XDG_DATA_HOME=str(private_home / "data"),
        SWORD_PATH=str(root),
        DISPLAY=":91",
        GDK_BACKEND="x11",
        NO_AT_BRIDGE="1",
        LC_ALL="C.UTF-8",
    )
    display = None
    app = None
    try:
        display = subprocess.Popen(
            ["Xvfb", ":91", "-screen", "0", "1280x800x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(1.5)
        if display.poll() is not None:
            raise PilotError("Xvfb failed before independent Xiphos GUI startup")
        app = subprocess.Popen(
            ["dbus-run-session", "--", "xiphos"], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(seconds * 2):
            if display.poll() is not None or app.poll() is not None:
                raise PilotError("Xiphos or isolated X11 display terminated prematurely")
            time.sleep(0.5)
        window = _visible_window(env)
        if not window:
            raise PilotError("No independently visible Xiphos GTK window")
        return {
            "real_xiphos_process_survived_bounded_startup": True,
            "real_xiphos_X11_window_found": True,
            "isolated_original_SWORD_PATH": True,
            "independent_commentary_text_actually_rendered_and_read": False,
            "independent_Xiphos_reference_navigation_verified": False,
            "AndBible_Android_GUI_tested": False,
            "screenshot_or_original_commentary_text_uploaded": False,
        }
    finally:
        if app is not None:
            _stop_group(app)
        if display is not None:
            _stop_group(display)


def observe_stock_xiphos(resource_id: str, *, seconds: int = 12) -> dict:
    manifest = load_manifest(resource_id)
    if (manifest["rights"]["status"] != "research_only"
            or manifest["rights"]["owner_approved"] is not False):
        raise PilotError("Only unapproved research-only pinned stock can be GUI-smoked")
    expected_zip = manifest.get("archive_sha256")
    expected_conf = manifest.get("stock_conf_sha256")
    if (not isinstance(expected_zip, str) or len(expected_zip) != 64
            or not isinstance(expected_conf, str) or len(expected_conf) != 64):
        raise PilotError("Original ZIP and .conf independently pinned SHA-256 required")
    with tempfile.TemporaryDirectory(prefix="commentary-stock-xiphos-private-") as tmp:
        work = Path(tmp)
        archive = work / "original-sword.zip"
        obtained = fetch(manifest["sword_zip_url"], archive, manifest["provider"])
        if obtained["sha256"] != expected_zip:
            raise PilotError("Original stock commentary ZIP fingerprint drifted")
        inspected = inspect_archive(
            archive, source_kind="sword", expected_module_id=manifest["module_id"],
            expected_category="commentary",
        )
        conf = inspected["sword_conf"]
        if (conf["driver"] != "zCom"
                or conf["version"] != manifest["version"]
                or conf["language"] != manifest["language"]
                or (conf["versification"] or "KJV") != "KJV"):
            raise PilotError("Stock SWORD zCom identity differs from pinned edition")
        with ZipFile(archive) as z:
            if sha256(z.read("mods.d/" + manifest["module_id"].lower() + ".conf")).hexdigest() != expected_conf:
                raise PilotError("Original exact SWORD .conf SHA-256 differs")
        root = work / "installed"
        _safe_stock_install(archive, inspected["members"], root)
        # Independent SWORD text-engine readback before opening the GTK UI.
        samples = []
        substantial = False
        for reference in manifest["sample_references"]:
            code, output = query(
                manifest["module_id"], reference, fmt="plain", root=root,
                exe="diatheke", limit=256 * 1024, timeout=30,
            )
            if code or not present_key(reference, output, code):
                raise PilotError("Installed exact stock entry unreadable in diatheke")
            substantial |= len(output) > 64
            samples.append(sha256(output).hexdigest())
        if not substantial:
            raise PilotError("No nontrivial original commentary entry was independently read")
        result = _probe_real_gui(root, seconds=seconds)
        return {
            "schema_version": 1,
            "status": "original_pinned_zCom_xiphos_real_window_private_smoke_pass",
            "resource_id": resource_id,
            "original_upstream_archive_sha256": obtained["sha256"],
            "original_upstream_conf_sha256": expected_conf,
            "original_module_id": manifest["module_id"],
            "original_sword_driver": "zCom",
            "diatheke_original_readback_sha256": samples,
            "original_stock_diatheke_samples_available": True,
            **result,
            "edition_equivalence_to_other_digital_witness": "unverified",
            "editorial_approved": False,
            "rights_approved": False,
            "published": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--seconds", type=int, default=12)
    parser.add_argument("--report", type=Path, required=True)
    a = parser.parse_args()
    if a.report.is_symlink() or a.report.exists() or not a.report.parent.is_dir():
        raise PilotError("Refusing existing/unsafe private Xiphos report path")
    report = observe_stock_xiphos(a.resource_id, seconds=a.seconds)
    a.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("Private original zCom Xiphos GUI process/window observed; no authorial content or screenshots exported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
