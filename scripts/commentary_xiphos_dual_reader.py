#!/usr/bin/env python3
"""Real isolated Xiphos reader with a reviewed Bible + exact stock commentary.

Uses a byte-attested repository Bible as the actual active reader context.
The commentary remains the unchanged SHA-256-pinned CrossWire zCom source.
Tries actual Xiphos keyboard navigation and reads only an ephemeral GTK
clipboard. It compares distinctive excerpts to private diatheke readback,
without uploading any biblical/commentary words or screenshots.

A window, keypress or changed clipboard alone is NOT text-rendering approval.
This is a narrow cross-reader test, not a release or editorial decision.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from zipfile import ZipFile

from commentary_intake import load_manifest
from commentary_native_raw_inventory import _safe_stock_install
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from pilot_subprocess import present_key, query
from reader_xiphos_headless_smoke import (
    _stop_group, _visible_window, _dismiss_transient_xiphos_notice,
    install_checked_out_rawtext_comparison,
)

ROOT = Path(__file__).resolve().parents[1]
BIBLE_ROOT = ROOT / "modules/lsg-1910/payload"
BIBLE_ATTESTATION = ROOT / "config/catalogue-import-lsg-0.1.0.json"
BIBLE_MODULE = "BRLSG1910"
BIBLE_V11N = "Segond"
# Actual authored comments are never copied into the version-controlled repository.
PASSAGES = ("Gen 1:1", "John 3:16", "Ps 23:1")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def verify_and_install_reviewed_bible(destination: Path, *, source: Path = BIBLE_ROOT,
                                     attestation: Path = BIBLE_ATTESTATION) -> dict:
    """Prove every existing published LSG member still equals its review receipt."""
    if (destination.is_symlink() or not destination.is_dir()
            or source.is_symlink() or not source.is_dir()
            or attestation.is_symlink() or not attestation.is_file()):
        raise PilotError("Unsafe or missing locally reviewed Bible source")
    evidence = json.loads(attestation.read_text(encoding="utf-8"))
    members = evidence.get("files", {})
    expected = {
        "mods.d/brlsg1910.conf",
        "modules/texts/rawtext/brlsg1910/ot",
        "modules/texts/rawtext/brlsg1910/ot.vss",
        "modules/texts/rawtext/brlsg1910/nt",
        "modules/texts/rawtext/brlsg1910/nt.vss",
    }
    if (evidence.get("module_id") != BIBLE_MODULE or
            set(members) != expected or
            not all(isinstance(x, str) and SHA.fullmatch(x) for x in members.values())):
        raise PilotError("Unreviewed Bible identity or payload inventory")
    for relative, digest in sorted(members.items()):
        original = source / relative
        if (original.is_symlink() or not original.is_file()
                or sha256(original.read_bytes()).hexdigest() != digest):
            raise PilotError("Reviewed Bible payload changed since source attestation")
    installed = install_checked_out_rawtext_comparison(
        source, destination, BIBLE_MODULE, BIBLE_V11N,
    )
    if installed["file_count"] != 5 or installed["module_id"] != BIBLE_MODULE:
        raise PilotError("Reviewed Bible was not independently installed")
    return {
        "module_id": BIBLE_MODULE,
        "version": evidence.get("release_tag"),
        "versification": BIBLE_V11N,
        "all_five_published_bible_files_sha256_attested": True,
    }


def _normalized_words(raw: bytes) -> list[str]:
    """Text comparison only; no rewriting of either actual SWORD module."""
    value = unicodedata.normalize("NFKD", raw.decode("utf-8", errors="replace"))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+", value.casefold())


def _long_commentary_excerpt_is_on_gui_clipboard(
    original_commentary: bytes, bible: bytes, clipboard: bytes,
) -> bool:
    """Require ≥15 consecutive distinctive words absent from Bible text.

    Checking a module name, short repeated Bible phrase or a window title
    alone must never yield false authorial content-rendering approval.
    """
    if (not isinstance(clipboard, bytes) or
            not 64 <= len(clipboard) <= 256_000):
        return False
    words = _normalized_words(original_commentary)
    bible_words = " ".join(_normalized_words(bible))
    copied_words = " ".join(_normalized_words(clipboard))
    if len(words) < 20 or len(copied_words) < 100:
        return False
    # Actual diatheke output starts with its own module/reference header.
    # The substantive offset avoids matching only names and passage labels.
    for offset in range(8, min(len(words) - 15, 220), 6):
        phrase = " ".join(words[offset:offset + 16])
        if (len(phrase) > 75 and phrase not in bible_words
                and phrase in copied_words):
            return True
    return False


def _x11(args: list[str], env: dict, *, input_bytes: bytes | None = None,
         timeout: int = 12) -> bytes:
    try:
        proc = subprocess.run(
            args, env=env, input=input_bytes, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PilotError("Bounded actual Xiphos reader UI action unavailable") from exc
    if proc.returncode != 0:
        raise PilotError("Actual Xiphos reader UI action failed")
    if len(proc.stdout) > 256_000:
        raise PilotError("Unbounded private Xiphos clipboard/window response")
    return proc.stdout


def _main_xiphos_window(env: dict) -> str | None:
    for query_command in (
        ["xdotool", "search", "--onlyvisible", "--class", "[Xx]iphos"],
        ["xdotool", "search", "--onlyvisible", "--name", "[Xx]iphos"],
    ):
        try:
            available = _x11(query_command, env)
        except PilotError:
            continue
        for line in available.decode("ascii", errors="ignore").splitlines():
            if not line.isdecimal():
                continue
            # Prevent accidentally selecting the tiny startup/notice dialog:
            try:
                geometry = _x11(
                    ["xdotool", "getwindowgeometry", "--shell", line], env,
                ).decode("ascii", errors="ignore")
            except PilotError:
                continue
            dims = dict(re.findall(r"^(WIDTH|HEIGHT)=(\d+)$", geometry, re.M))
            if int(dims.get("WIDTH", "0")) >= 500 and int(dims.get("HEIGHT", "0")) >= 350:
                return line
    return None


def attempt_real_xiphos_passage_copy(env: dict, comparisons: dict[str, dict]) -> dict:
    """Actual GUI passage changes in Bible + commentary pane (Alt+C).

    Absence of copyable text remains an honest PENDING, not a module defect.
    """
    if env.get("DISPLAY") != ":91" or env.get("GDK_BACKEND") != "x11":
        raise PilotError("Unsafe virtual reader display")
    window = _main_xiphos_window(env)
    if window is None:
        return {"real_main_reader_window_found": False,
                "actual_passage_commands_accepted": False,
                "commentary_clipboard_match_by_passage": {
                    key: False for key in comparisons
                },
                "independent_gui_commentary_excerpt_match_count": 0}
    result = {}
    accepted = True
    for ref, originals in comparisons.items():
        try:
            _x11(["xdotool", "windowfocus", "--sync", window], env)
            for command in (
                ["xdotool", "key", "--clearmodifiers", "ctrl+l"],
                ["xdotool", "type", "--clearmodifiers", "--delay", "25", ref],
                ["xdotool", "key", "Return"],
                ["xdotool", "key", "--clearmodifiers", "alt+c"],
            ):
                _x11(command, env)
            time.sleep(2)
            # Replace prior clipboard content before copying to ensure that
            # stale text from an earlier chapter cannot produce a false PASS.
            _x11(["xclip", "-selection", "clipboard", "-i"], env, input_bytes=b"")
            _x11(["xdotool", "key", "--clearmodifiers", "ctrl+a"], env)
            _x11(["xdotool", "key", "--clearmodifiers", "ctrl+c"], env)
            time.sleep(1)
            selected = _x11(["xclip", "-selection", "clipboard", "-o"], env)
            result[ref] = _long_commentary_excerpt_is_on_gui_clipboard(
                originals["commentary"], originals["bible"], selected
            )
        except PilotError:
            accepted = False
            result[ref] = False
    return {
        "real_main_reader_window_found": True,
        "actual_passage_commands_accepted": accepted,
        "commentary_clipboard_match_by_passage": result,
        "independent_gui_commentary_excerpt_match_count": sum(result.values()),
    }


def _run_real_gui(root: Path, comparisons: dict[str, dict], *, seconds: int) -> dict:
    if (not 6 <= seconds <= 25 or root.is_symlink() or not root.is_dir()
            or not (root / "mods.d/mhcc.conf").is_file()
            or not (root / "mods.d/brlsg1910.conf").is_file()):
        raise PilotError("Xiphos requires pinned Bible plus original commentary")
    for program in ("Xvfb", "dbus-run-session", "xiphos", "xdotool", "xclip"):
        if shutil.which(program) is None:
            raise PilotError("Real Xiphos dual-module reader dependency unavailable")
    home = root.parent / "independent-xiphos-home"
    if home.exists() or home.is_symlink():
        raise PilotError("Refusing reused GUI test HOME")
    home.mkdir(mode=0o700)
    for name in ("config", "cache", "data"):
        (home / name).mkdir()
    env = dict(
        os.environ, HOME=str(home),
        XDG_CONFIG_HOME=str(home / "config"),
        XDG_CACHE_HOME=str(home / "cache"),
        XDG_DATA_HOME=str(home / "data"),
        SWORD_PATH=str(root), DISPLAY=":91",
        GDK_BACKEND="x11", LC_ALL="C.UTF-8",
        NO_AT_BRIDGE="1",
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
            raise PilotError("Actual virtual Xiphos display did not start")
        app = subprocess.Popen(
            ["dbus-run-session", "--", "xiphos"], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(seconds * 2):
            if app.poll() is not None or display.poll() is not None:
                raise PilotError("Independent reader or X11 display ended unexpectedly")
            time.sleep(0.5)
        if not _visible_window(env):
            raise PilotError("No independently visible Xiphos window with Bible and commentary")
        _dismiss_transient_xiphos_notice(env)
        inspection = attempt_real_xiphos_passage_copy(env, comparisons)
        return {
            "real_xiphos_executable_started_and_visible": True,
            "original_source_SWORD_PATH_isolated": True,
            **inspection,
        }
    finally:
        if app is not None:
            _stop_group(app)
        if display is not None:
            _stop_group(display)


def observe_dual_module_reader(resource_id: str = "mhcc-crosswire",
                               *, seconds: int = 12) -> dict:
    manifest = load_manifest(resource_id)
    if (manifest["rights"]["status"] != "research_only"
            or manifest["rights"]["owner_approved"] is not False
            or manifest["module_id"] != "MHCC"):
        raise PilotError("Only pinned, unapproved original MHCC used for this pilot")
    for field in ("archive_sha256", "stock_conf_sha256"):
        if not isinstance(manifest.get(field), str) or not SHA.fullmatch(manifest[field]):
            raise PilotError("Exact original commentary fingerprints required")
    with tempfile.TemporaryDirectory(prefix="commentary-xiphos-dual-private-") as directory:
        temp = Path(directory)
        archive = temp / "original-crosswire.zip"
        obtained = fetch(manifest["sword_zip_url"], archive, manifest["provider"])
        if obtained["sha256"] != manifest["archive_sha256"]:
            raise PilotError("Original CrossWire MHCC ZIP fingerprint drift")
        inspection = inspect_archive(
            archive, source_kind="sword", expected_module_id=manifest["module_id"],
            expected_category="commentary",
        )
        conf = inspection["sword_conf"]
        if (conf["driver"] != "zCom" or conf["version"] != manifest["version"]
                or conf["language"] != manifest["language"]
                or (conf["versification"] or "KJV") != "KJV"):
            raise PilotError("Original MHCC stock identity/versification drift")
        with ZipFile(archive) as z:
            metadata = z.read("mods.d/" + manifest["module_id"].lower() + ".conf")
        if sha256(metadata).hexdigest() != manifest["stock_conf_sha256"]:
            raise PilotError("Original module configuration SHA-256 differs")
        installed = temp / "sword-library"
        _safe_stock_install(archive, inspection["members"], installed)
        bible = verify_and_install_reviewed_bible(installed)
        comparisons = {}
        for passage in PASSAGES:
            pair = {}
            for slot, module in (("commentary", manifest["module_id"]),
                                 ("bible", BIBLE_MODULE)):
                code, output = query(
                    module, passage, fmt="plain", root=installed,
                    exe="diatheke", limit=256 * 1024, timeout=30,
                )
                key_found = present_key(passage, output, code)
                threshold = 64 if slot == "commentary" else 16
                if code != 0 or not key_found or len(output) <= threshold:
                    # Metadata-only diagnostic: no Bible/commentary words or
                    # source fragments leave the private runner.
                    raise PilotError(
                        f"Actual installed {slot} entry unreadable at {passage}: "
                        f"exit_success={code == 0}; key_found={key_found}; "
                        f"output_bytes={len(output)}; threshold={threshold}"
                    )
                pair[slot] = output
            comparisons[passage] = pair
        observed = _run_real_gui(installed, comparisons, seconds=seconds)
        return {
            "schema_version": 1,
            "status": "pinned_original_MHCC_plus_attested_Bible_real_Xiphos_reader_probe",
            "resource_id": resource_id,
            "exact_original_commentary_zip_sha256": obtained["sha256"],
            "exact_original_commentary_conf_sha256": sha256(metadata).hexdigest(),
            "original_module_id": manifest["module_id"],
            "installed_reviewed_bible": bible,
            "both_real_sword_modules_have_nonempty_diatheke_readback": True,
            "sample_count": len(comparisons),
            **observed,
            "entire_original_commentary_content_and_links_gui_verified": False,
            "owner_rights_editorial_approval": False,
            "published": False,
            "commentary_or_bible_text_uploaded": False,
            "screenshots_uploaded": False,
        }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id", default="mhcc-crosswire")
    p.add_argument("--seconds", type=int, default=12)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        raise PilotError("Unsafe or preexisting Xiphos receipt path")
    result = observe_dual_module_reader(args.resource_id, seconds=args.seconds)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Original MHCC and reviewed Bible tested in real isolated Xiphos; no source prose/screenshots exported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
