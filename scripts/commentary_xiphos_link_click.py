#!/usr/bin/env python3
"""PRIVATE, bounded Xiphos mouse-click experiment on an authentic stock OSIS link.

This is not a claim of navigation unless the *real* Bible pane changes to
independently queried, source-attested target prose. Original words, screenshots,
link labels and private SWORD ZIPs never leave the disposable CI runner.
"""
from __future__ import annotations

import ctypes
import ctypes.util
from hashlib import sha256
from html import unescape
import re
import time
from urllib.parse import unquote

from commentary_xiphos_dual_reader import (
    _BoundedMarkupScanner, _OSIS_REF_ATTRIBUTE, _REFERENCE_WITH_ATTRIBUTES,
    _commentary_pane_focus_points, _main_xiphos_window, _normalized_words,
    _optional_real_rich_xiphos_selection, _seed_x11_clipboard, _x11,
)
from pilot_subprocess import query, present_key
from pilot_preflight import PilotError

_OSIS = re.compile(r"([1-4]?[A-Za-z][A-Za-z0-9]*)\.([1-9][0-9]{0,2})\.([1-9][0-9]{0,2})\Z")
_REF = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]* [1-9][0-9]{0,2}:[1-9][0-9]{0,2}\Z")
_MAX_LINKS = 24


def _real_original_targets(
    original: bytes, rich: bytes, source_ref: str, *, diagnostics: dict | None = None,
) -> list[str]:
    """Join exact original OSIS targets + authorial labels to actual GUI hrefs."""
    if (not isinstance(original, bytes) or not isinstance(rich, bytes)
            or len(original) > 256_000 or len(rich) > 256_000
            or not _REF.fullmatch(source_ref)):
        raise PilotError("Unsafe private original link evidence")
    scan = _BoundedMarkupScanner()
    scan.feed(rich.decode("utf-8", errors="replace"))
    source_chapter = source_ref.split(":", 1)[0]
    targets = []
    source_refs = _REFERENCE_WITH_ATTRIBUTES.findall(
        original.decode("utf-8", errors="replace")
    )[:256]
    if diagnostics is not None:
        diagnostics["real_GUI_rich_anchor_count"] += len(scan.anchor_destinations)
        diagnostics["original_source_reference_elements_count"] += len(source_refs)
    for attrs, body in source_refs:
        attr = _OSIS_REF_ATTRIBUTE.search(attrs)
        if attr is None:
            continue
        raw = unescape(attr.group(2)).strip()
        if raw.startswith("Bible:"):
            raw = raw[len("Bible:"):]
        match = _OSIS.fullmatch(raw)
        if not match:
            if diagnostics is not None:
                diagnostics["non_single_OSIS_original_reference_count"] += 1
            continue  # no guessed range/multitarget-to-verse mapping
        if diagnostics is not None:
            diagnostics["single_OSIS_original_reference_count"] += 1
        book, chapter, verse = match.groups()
        reference = f"{book} {chapter}:{verse}"
        if f"{book} {chapter}" == source_chapter:
            if diagnostics is not None:
                diagnostics["same_chapter_original_reference_count"] += 1
            continue  # target could already be in current full chapter
        label_parser = _BoundedMarkupScanner()
        label_parser.feed(unescape(body))
        label = " ".join("".join(label_parser.text_chunks).split())
        if len(label) < 5:
            if diagnostics is not None:
                diagnostics["short_original_reference_label_count"] += 1
            continue
        escaped_target = raw.casefold()
        matching = [
            unquote(unescape(href)).casefold()
            for seen_label, href in scan.anchor_destinations
            if seen_label == label and re.search(
                r"(?<![a-z0-9])" + re.escape(escaped_target) + r"(?![a-z0-9])",
                unquote(unescape(href)).casefold(),
            )
        ]
        if diagnostics is not None:
            diagnostics["exact_authorial_label_and_href_target_joins"] += len(matching)
        # Xiphos's own main_url_handler supports sword/bible URI and
        # passagestudy.jsp / xiphos.url. Do not click an arbitrary external URL.
        if not any(uri.startswith((
            "sword://", "bible://", "passagestudy.jsp", "xiphos.url",
        )) for uri in matching):
            if diagnostics is not None:
                diagnostics["single_source_target_not_joined_to_GUI_count"] += 1
                diagnostics["source_target_href_scheme_not_approved_count"] += (
                    1 if matching else 0
                )
            continue
        if reference not in targets:
            targets.append(reference)
        if len(targets) >= _MAX_LINKS:
            break
    return targets


def _has_target_phrase(original_verse_readback: bytes, gui_copy: bytes,
                       before_click: bytes) -> bool:
    """A distinctive *original Bible target* ten-word sequence was newly shown."""
    if (max(len(original_verse_readback), len(gui_copy), len(before_click))
            > 256_000):
        raise PilotError("Unsafe Bible-pane original verse witness size")
    words = _normalized_words(original_verse_readback)
    after = _normalized_words(gui_copy)
    before = _normalized_words(before_click)
    # Ignore module/verse headers in diatheke. Verse content is independent
    # of the commentary's labels and of previously displayed Bible text.
    if len(words) < 14 or len(after) < 12:
        return False
    for k in range(6, len(words) - 9):
        p = words[k:k + 10]
        if (len(" ".join(p)) >= 55
                and any(after[i:i + 10] == p for i in range(len(after)-9))
                and not any(before[i:i + 10] == p for i in range(len(before)-9))):
            return True
    return False


class _XFixesCursor:
    """Read pointer *shape* only via the X11 XFixes extension; no pixels logged."""
    class _Image(ctypes.Structure):
        _fields_ = [
            ("x", ctypes.c_short), ("y", ctypes.c_short),
            ("width", ctypes.c_ushort), ("height", ctypes.c_ushort),
            ("xhot", ctypes.c_ushort), ("yhot", ctypes.c_ushort),
            ("cursor_serial", ctypes.c_ulong),
            ("pixels", ctypes.POINTER(ctypes.c_ulong)),
            ("atom", ctypes.c_ulong), ("name", ctypes.c_char_p),
        ]

    def __init__(self):
        xlib = ctypes.util.find_library("X11")
        fixlib = ctypes.util.find_library("Xfixes")
        if not xlib or not fixlib:
            raise PilotError("X11 pointer shape inspection unavailable")
        self.x = ctypes.CDLL(xlib)
        self.fx = ctypes.CDLL(fixlib)
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.x.XFree.argtypes = [ctypes.c_void_p]
        self.x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.fx.XFixesGetCursorImage.argtypes = [ctypes.c_void_p]
        self.fx.XFixesGetCursorImage.restype = ctypes.POINTER(self._Image)
        self.display = self.x.XOpenDisplay(b":91")
        if not self.display:
            raise PilotError("Private X11 cursor shape display unavailable")

    def read(self) -> tuple[str, str]:
        data = self.fx.XFixesGetCursorImage(self.display)
        if not data:
            raise PilotError("XFixes cursor shape unavailable")
        try:
            info = data.contents
            if not 1 <= info.width <= 128 or not 1 <= info.height <= 128:
                raise PilotError("Unbounded X11 cursor image")
            payload = ctypes.string_at(
                info.pixels, info.width * info.height * ctypes.sizeof(ctypes.c_ulong)
            )
            name = info.name.decode("utf-8", errors="replace") if info.name else ""
            return (name.casefold(), sha256(payload).hexdigest())
        finally:
            self.x.XFree(ctypes.cast(data, ctypes.c_void_p))

    def close(self):
        if self.display:
            self.x.XCloseDisplay(self.display)
            self.display = None


def _real_bible_clipboard(env: dict, window: str) -> bytes:
    geo = _x11(["xdotool", "getwindowgeometry", "--shell", window], env)
    values = dict(re.findall(rb"^(X|Y|WIDTH|HEIGHT)=(-?\d+)$", geo, re.M))
    if set(values) != {b"X", b"Y", b"WIDTH", b"HEIGHT"}:
        raise PilotError("No verified Xiphos Bible pane geometry")
    x, y, w, h = (int(values[k]) for k in
                   (b"X", b"Y", b"WIDTH", b"HEIGHT"))
    if (x < 0 or y < 0 or not 700 <= w <= 1280 or not 500 <= h <= 800
            or x + w > 1280 or y + h > 800):
        raise PilotError("Out-of-bounds private Xiphos Bible pane")
    _x11(["xdotool", "mousemove", str(x+w*32//100),
          str(y+h*41//100), "click", "1"], env)
    _seed_x11_clipboard(env)
    _x11(["xdotool", "key", "--clearmodifiers", "ctrl+a"], env)
    _x11(["xdotool", "key", "--clearmodifiers", "ctrl+c"], env)
    time.sleep(.35)
    return _x11(["xclip", "-selection", "clipboard", "-o"], env)


def _show_source(env: dict, window: str, ref: str):
    if not _REF.fullmatch(ref):
        raise PilotError("Unreviewed real reader source passage")
    _x11(["xdotool", "windowfocus", "--sync", window], env)
    for cmd in (
        ["xdotool", "key", "--clearmodifiers", "ctrl+l"],
        ["xdotool", "type", "--clearmodifiers", "--delay", "15", ref],
        ["xdotool", "key", "Return"],
        ["xdotool", "key", "--clearmodifiers", "alt+c"],
    ):
        _x11(cmd, env)
    time.sleep(.65)


def probe_real_original_osisref_click(
    env: dict, original_source_comparisons: dict, original_link_keys: list[str],
    *, installed_sword_root,
) -> dict:
    """Try real pointer clicks; return only source-safe, text-free result classes.

    A GUI click is proven ONLY if the independently read genuine Bible target
    has newly appeared in the actual *Bible pane* after the click. A mere href,
    pointer cursor, key press or changed window never counts as navigation.
    """
    base = {
        "scope": "real_isolated_xiphos_mouse_on_original_source_link",
        "source_reference_targets_verified_in_real_GUI": False,
        "real_GUI_rich_selection_available_count": 0,
        "real_GUI_rich_anchor_count": 0,
        "original_source_reference_elements_count": 0,
        "single_OSIS_original_reference_count": 0,
        "non_single_OSIS_original_reference_count": 0,
        "same_chapter_original_reference_count": 0,
        "short_original_reference_label_count": 0,
        "single_source_target_not_joined_to_GUI_count": 0,
        "exact_authorial_label_and_href_target_joins": 0,
        "source_target_href_scheme_not_approved_count": 0,
        "independent_exact_target_bible_readbacks": 0,
        "x11_pointer_shape_observed": False,
        "hover_candidate_actual_mouse_clicks": 0,
        "genuine_original_osisref_click_navigated_to_expected_bible": False,
        "status": "inconclusive_no_eligible_authentic_GUI_link",
        "original_words_or_private_screenshots_exported": False,
    }
    if (env.get("DISPLAY") != ":91" or env.get("GDK_BACKEND") != "x11"
            or not installed_sword_root.is_dir()
            or not isinstance(original_link_keys, list)
            or not 1 <= len(original_link_keys) <= 3):
        raise PilotError("Unapproved original real reader mouse context")
    window = _main_xiphos_window(env)
    if window is None:
        base["status"] = "real_xiphos_main_window_unavailable"
        return base
    try:
        points = _commentary_pane_focus_points(env, window)
    except PilotError:
        base["status"] = "commentary_pane_geometry_unavailable"
        return base
    pointer = None
    try:
        pointer = _XFixesCursor()
        base["x11_pointer_shape_observed"] = True
    except PilotError:
        base["status"] = "X11_pointer_shape_unavailable"
        return base
    try:
        for source_ref in original_link_keys:
            source = original_source_comparisons.get(source_ref)
            if not isinstance(source, dict):
                continue
            _show_source(env, window, source_ref)
            _x11(["xdotool", "mousemove", str(points[0][0]),
                  str(points[0][1]), "click", "1"], env)
            _seed_x11_clipboard(env)
            _x11(["xdotool", "key", "--clearmodifiers", "ctrl+a"], env)
            _x11(["xdotool", "key", "--clearmodifiers", "ctrl+c"], env)
            time.sleep(.35)
            rich = _optional_real_rich_xiphos_selection(env)
            if not rich:
                continue
            base["real_GUI_rich_selection_available_count"] += 1
            targets = _real_original_targets(
                source["commentary_internal"], rich, source_ref,
                diagnostics=base,
            )
            if not targets:
                continue
            original_target_bibles = {}
            for target in targets:
                code, plain = query("BRLSG1910", target, fmt="plain",
                    root=installed_sword_root, exe="diatheke",
                    limit=256 * 1024, timeout=20)
                if code == 0 and present_key(target, plain, code) and len(plain) >= 75:
                    original_target_bibles[target] = plain
            if not original_target_bibles:
                continue
            base["independent_exact_target_bible_readbacks"] += len(original_target_bibles)
            before = _real_bible_clipboard(env, window)
            candidates = {
                ref: data for ref, data in original_target_bibles.items()
                if _has_target_phrase(data, data, before)
            }
            if not candidates:
                continue
            base["source_reference_targets_verified_in_real_GUI"] = True
            base["status"] = "genuine_source_href_attested_mouse_link_not_yet_confirmed"
            _show_source(env, window, source_ref)
            x0, y0 = points[0]
            # Deliberately bounded to the already verified right commentary
            # area. Never click toolbar, menus, a desktop or external browser.
            coords = [(x0 + dx, y0 + dy)
                      for dy in (-205, -160, -115, -70, -25, 20, 65, 110, 155)
                      for dx in (-185, -135, -85, -35, 15, 65)]
            for xx, yy in coords:
                if not 0 < xx < 1280 or not 0 < yy < 800:
                    continue
                _x11(["xdotool", "mousemove", str(xx), str(yy)], env)
                time.sleep(.045)
                name, fp = pointer.read()
                # Actual X11 hyperlink hover cursor; the pointer's name is
                # diagnostic, not proof of source target or click navigation.
                if not any(x in name for x in ("hand", "pointer", "link")):
                    continue
                _x11(["xdotool", "click", "1"], env)
                base["hover_candidate_actual_mouse_clicks"] += 1
                time.sleep(.5)
                after = _real_bible_clipboard(env, window)
                if any(_has_target_phrase(data, after, before)
                       for data in candidates.values()):
                    base["genuine_original_osisref_click_navigated_to_expected_bible"] = True
                    base["status"] = "original_source_attested_link_real_click_Bible_target_verified"
                    return base
                if base["hover_candidate_actual_mouse_clicks"] >= 12:
                    return base
                _show_source(env, window, source_ref)
            return base
        return base
    except PilotError:
        base["status"] = "real_GUI_pointer_or_bible_readback_unavailable"
        return base
    finally:
        pointer.close()
