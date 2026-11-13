#!/usr/bin/env python3
"""PRIVATE real-Xiphos commentary book/chapter-introduction context-menu probe.

Use original, full-native-corpus SHA-pinned SWORD intro entries and actual X11
menu/clipboard interaction. The result is metadata only. An unsuccessful menu
attempt is INCONCLUSIVE, never evidence of missing upstream commentary text.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata

from lxml import etree

from commentary_xiphos_dual_reader import (
    _commentary_pane_focus_points, _main_xiphos_window, _seed_x11_clipboard,
    _x11,
)
from pilot_preflight import PilotError
from sword_native_raw_corpus_inventory import parse_native_raw_corpus

_SHA = re.compile(r"[a-f0-9]{64}\Z")
_BOOK = "Gen"
_CHAPTER = "Gen.1"
_REF = "Gen 1:1"


def pinned_source_intro_witness(
    source_root: Path, original_id: str, scanner: Path,
    *, expected_raw_corpus_sha256: str,
) -> dict[str, bytes]:
    """Return original source I entries privately; do not serialize any raw data."""
    if (not source_root.is_dir() or source_root.is_symlink()
            or not scanner.is_file() or scanner.is_symlink()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", original_id)
            or not _SHA.fullmatch(expected_raw_corpus_sha256)):
        raise PilotError("Unreviewed original commentary intro source or scanner")
    found: dict[str, bytes] = {}
    def observe(kind: str, key: str, raw: bytes):
        if kind == "I" and key in {_BOOK, _BOOK+".0.0", _CHAPTER, _CHAPTER+".0"}:
            found[key] = raw
    proc = None
    try:
        proc = subprocess.Popen(
            ["timeout", "300s", str(scanner), original_id],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=dict(os.environ, SWORD_PATH=str(source_root)),
        )
        if proc.stdout is None:
            raise PilotError("Original commentary intro stream unavailable")
        report, _, _, _ = parse_native_raw_corpus(proc.stdout, on_entry=observe)
        proc.stdout.close()
        code = proc.wait(timeout=15)
        if code or report["all_native_raw_entries_ordered_sha256"] != expected_raw_corpus_sha256:
            raise PilotError("Actual native commentary intro stream SHA drift")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PilotError("Original intro source scanner unavailable") from exc
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            if proc.stdout is not None:
                proc.stdout.close()
    result = {}
    for key, raw in found.items():
        if not 1 <= len(raw) <= 2_000_000:
            continue
        try:
            parsed = etree.fromstring(
                b"<source>" + raw + b"</source>",
                parser=etree.XMLParser(
                    resolve_entities=False, no_network=True,
                    load_dtd=False, recover=False, huge_tree=False,
                ),
            )
        except (ValueError, etree.XMLSyntaxError):
            continue
        if any(isinstance(x, etree._Entity) for x in parsed.iter()):
            continue
        words = _words("".join(parsed.itertext()))
        if len(words) >= 10:
            result["book" if key in {_BOOK, _BOOK+".0.0"} else "chapter"] = raw
    return result


def _words(text: str) -> list[str]:
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(x for x in norm if not unicodedata.combining(x))
    return re.findall(r"[a-z0-9]+", norm.casefold())


def _intro_in_gui_clipboard(intro: bytes, copied: bytes, verse_text: bytes) -> bool:
    """A real 10+ consecutive ORIGINAL intro word run absent from verse prose."""
    if not isinstance(intro, bytes) or not isinstance(copied, bytes):
        raise PilotError("Unbounded source intro/GUI clipboard witness")
    if max(len(intro), len(copied), len(verse_text)) > 2_000_000:
        raise PilotError("Unbounded original intro comparison")
    parsed = etree.fromstring(
        b"<source>" + intro + b"</source>",
        parser=etree.XMLParser(
            resolve_entities=False, no_network=True,
            load_dtd=False, recover=False, huge_tree=False,
        ),
    )
    source = _words("".join(parsed.itertext()))
    displayed = _words(copied.decode("utf-8", errors="replace"))
    verse = _words(verse_text.decode("utf-8", errors="replace"))
    if len(source) < 10 or len(displayed) < 10:
        return False
    for n in range(len(source) - 9):
        phrase = source[n:n+10]
        # Selection must be explanatory intro prose and must not be merely
        # the unchanged currently displayed first verse commentary.
        if (any(displayed[k:k+10] == phrase for k in range(len(displayed)-9))
                and not any(verse[k:k+10] == phrase for k in range(max(0,len(verse)-9)))):
            return True
    return False


def probe_real_xiphos_commentary_heading_menu(
    env: dict, private_intro_raw: dict[str, bytes], *,
    ordinary_first_verse: bytes,
) -> dict:
    """Best-effort bounded UI observation; false is NOT a missing-content verdict.

    GTK3 commentary menu source has a trailing 'Read Selection Aloud' item.
    The preceding two visible COMMENTARY_TYPE items are chapter and book
    headings. Navigate from End using Up, rather than assuming coordinates
    for a popup whose positioning depends on GTK theme.
    """
    if (env.get("DISPLAY") != ":91" or env.get("GDK_BACKEND") != "x11"
            or not isinstance(private_intro_raw, dict)
            or not isinstance(ordinary_first_verse, bytes)):
        raise PilotError("Unreviewed private Xiphos heading menu context")
    window = _main_xiphos_window(env)
    stats: dict[str, dict] = {}
    if window is None:
        return {"heading_context_real_main_reader_window_found": False,
                "book_and_chapter_menu_observations": {},
                "heading_GUI_presentation_verified": False,
                "intro_data_or_clipboard_exported": False,
                "no_heading_missing_from_source_inferred": True}
    try:
        points = _commentary_pane_focus_points(env, window)
    except PilotError:
        points = ()
    for kind, up in (("chapter", 1), ("book", 2)):
        status = "not_attempted"
        original = private_intro_raw.get(kind)
        if original is None:
            status = "no_authenticated_original_intro_key_for_this_scope"
        elif not points:
            status = "commentary_pane_geometry_unavailable"
        else:
            try:
                _x11(["xdotool", "windowfocus", "--sync", window], env)
                for cmd in (
                    ["xdotool", "key", "--clearmodifiers", "ctrl+l"],
                    ["xdotool", "type", "--clearmodifiers", "--delay", "25", _REF],
                    ["xdotool", "key", "Return"],
                    ["xdotool", "key", "--clearmodifiers", "alt+c"],
                ):
                    _x11(cmd, env)
                time.sleep(1)
                x,y = points[0]
                _x11(["xdotool", "mousemove", str(x), str(y), "click", "3"], env)
                time.sleep(.3)
                _x11(["xdotool", "key", "--clearmodifiers", "End"], env)
                for _ in range(up):
                    _x11(["xdotool", "key", "Up"], env)
                _x11(["xdotool", "key", "Return"], env)
                time.sleep(.6)
                _seed_x11_clipboard(env)
                _x11(["xdotool", "key", "--clearmodifiers", "ctrl+a"], env)
                _x11(["xdotool", "key", "--clearmodifiers", "ctrl+c"], env)
                time.sleep(.6)
                copied = _x11(["xclip", "-selection", "clipboard", "-o"], env)
                status = ("original_intro_prose_copied_from_real_GUI"
                          if _intro_in_gui_clipboard(original, copied, ordinary_first_verse)
                          else "menu_action_attempted_but_intro_not_proven_in_clipboard")
            except PilotError:
                status = "real_GUI_menu_or_clipboard_action_unavailable"
        stats[kind] = {"original_intro_sha256_attested": original is not None,
                       "GUI_menu_observation_class": status}
    return {
        "heading_context_real_main_reader_window_found": True,
        "book_and_chapter_menu_observations": stats,
        "heading_GUI_presentation_verified": all(
            x["GUI_menu_observation_class"] == "original_intro_prose_copied_from_real_GUI"
            for x in stats.values()
        ),
        "intro_data_or_clipboard_exported": False,
        "no_heading_missing_from_source_inferred": True,
    }
