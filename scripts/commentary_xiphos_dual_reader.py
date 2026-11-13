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
from html import unescape
from html.parser import HTMLParser
from urllib.parse import unquote
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
from commentary_stock_candidate import _reader_identity_only_equivalence
from commentary_reference_cross_slot import actual_stock_osisref_targets
from sword_native_raw_corpus_inventory import parse_native_raw_corpus, RawCorpusError
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
MAX_SUBSTANTIVE_SAMPLES = 3


def _candidate_passages(manifest: dict) -> tuple[str, ...]:
    """Probe only reviewed real source refs and their own chapter starts.

    A zCom commentary is legitimately sparse: an occupied chapter/range
    anchor need not occur at each Bible verse. Do not generate absent entries
    or label a silent stock slot as damaged. The full corpus is independently
    inventoried elsewhere.
    """
    refs = manifest["sample_references"]
    result = []
    for ref in refs:
        if not isinstance(ref, str):
            raise PilotError("Unreviewed source reference")
        match = re.fullmatch(r"([1-4]?[A-Za-z][A-Za-z ]{0,35}) ([1-9][0-9]{0,2}):([1-9][0-9]{0,2})", ref)
        if not match:
            raise PilotError("Malformed original commentary sample reference")
        book, chapter, verse = match.groups()
        for candidate in (ref, f"{book} {chapter}:1"):
            if candidate not in result:
                result.append(candidate)
    return tuple(result)
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


def _exact_native_commentary_raw(root: Path, module_id: str, ref: str,
                                 inspector: Path) -> bytes:
    """Read actual original stock XML through released libSWORD, no retyping.

    The full raw keys and all 29,975 occupied entries were previously audited.
    This small bounded private reader preserves markup needed for GUI title and
    scripture-link comparison without logging any original authorial content.
    """
    if (root.is_symlink() or not root.is_dir()
            or inspector.is_symlink() or not inspector.is_file()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", module_id)
            or not re.fullmatch(
                r"[1-4]?[A-Za-z][A-Za-z ]{0,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}", ref
            )):
        raise PilotError("Unsafe original native commentary inspection input")
    try:
        completed = subprocess.run(
            [str(inspector), module_id, ref],
            env=dict(os.environ, SWORD_PATH=str(root)),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PilotError("Original native commentary entry unavailable") from exc
    if completed.returncode or not 8 <= len(completed.stdout) <= 256_000:
        raise PilotError(
            "Actual original native commentary XML missing or outside safe bounds"
        )
    return completed.stdout


def _original_stock_reference_bearing_samples(
    root: Path, module_id: str, native_scanner: Path,
    *, expected_corpus_sha256: str, max_samples: int = 3,
) -> dict:
    """Reuse the existing FULL native SWORD scanner for real reference cases.

    This examines every occupied stock entry, chooses at most one actual
    strict-XML scripture-link-bearing key per source book, and verifies the
    entire native corpus digest again. No original XML/body/link target
    is ever returned to the CI receipt.
    """
    if (root.is_symlink() or not root.is_dir()
            or native_scanner.is_symlink() or not native_scanner.is_file()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", module_id)
            or not SHA.fullmatch(expected_corpus_sha256)
            or type(max_samples) is not int or not 1 <= max_samples <= 6):
        raise PilotError("Unreviewed source reference scan context")
    chosen = []
    observed_books = set()
    reference_bearing = 0
    strict_source_reference_parse_failures = 0

    def original_entry(kind: str, key: str, raw: bytes):
        nonlocal reference_bearing, strict_source_reference_parse_failures
        if kind != "K" or b"<reference" not in raw:
            return
        reference_bearing += 1
        try:
            original_targets = actual_stock_osisref_targets(raw)
        except PilotError:
            strict_source_reference_parse_failures += 1
            return
        if not original_targets or len(chosen) >= max_samples:
            return
        parts = key.split(".")
        if len(parts) != 3:
            return
        book, chapter, verse = parts
        if book in observed_books:
            return
        ref = f"{book} {chapter}:{verse}"
        if not re.fullmatch(
            r"[1-4]?[A-Za-z][A-Za-z ]{0,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}", ref
        ):
            return
        observed_books.add(book)
        chosen.append(ref)

    environment = dict(os.environ, SWORD_PATH=str(root))
    process = None
    try:
        process = subprocess.Popen(
            ["timeout", "300s", str(native_scanner), module_id],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=environment,
        )
        if process.stdout is None:
            raise PilotError("Original native corpus stream unavailable")
        inventory, _, _, _ = parse_native_raw_corpus(
            process.stdout, on_entry=original_entry
        )
        process.stdout.close()
        status = process.wait(timeout=15)
        if (status != 0 or
                inventory["all_native_raw_entries_ordered_sha256"] != expected_corpus_sha256):
            raise PilotError("Original corpus inventory or full native SHA-256 diverged")
    except (OSError, subprocess.TimeoutExpired, RawCorpusError) as exc:
        raise PilotError("Private original source link inventory failed") from exc
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
    return {
        "complete_native_original_stock_entries_checked": inventory["all_actual_raw_entries_scanned"],
        "full_pinned_raw_corpus_sha256_reconfirmed": True,
        "original_occupied_numbered_keys_with_reference_markup": reference_bearing,
        "original_stock_reference_strict_xml_parse_failures":
            strict_source_reference_parse_failures,
        "real_reference_bearing_original_native_samples": chosen,
        "actual_link_click_and_target_verified_in_xiphos": False,
        "original_authorial_reference_targets_exported": False,
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



# Read-only diagnostic of original stock OSIS markup and actual Xiphos clipboard.
# No source heading, authorial phrase, reference label or target leaves CI.
_TITLE_TAG = re.compile(r"<title(?:\s+[^>]*)?>(.*?)</title\s*>", re.I | re.S)
_REFERENCE_TAG = re.compile(r"<reference(?:\s+[^>]*)?>", re.I | re.S)
_REFERENCE_WITH_LABEL = re.compile(r"<reference(?:\s+[^>]*)?>(.*?)</reference\s*>", re.I | re.S)
_REFERENCE_WITH_ATTRIBUTES = re.compile(
    r"<reference\b([^>]*)>(.*?)</reference\s*>", re.I | re.S
)
_OSIS_REF_ATTRIBUTE = re.compile(r"\bosisRef\s*=\s*([\"'])(.*?)\1", re.I | re.S)


class _BoundedMarkupScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.link_count = 0
        self.text_chunks = []
        self.anchor_labels = []
        self.anchor_destinations = []
        self._current_anchor = None
        self._current_href = None

    def handle_starttag(self, tag, attrs):
        if tag.casefold() == "a":
            href = next((
                value for key, value in attrs
                if key.casefold() == "href" and isinstance(value, str) and value.strip()
            ), None)
            if href is not None:
                self.link_count += 1
                self._current_anchor = []
                self._current_href = href

    def handle_endtag(self, tag):
        if tag.casefold() == "a" and self._current_anchor is not None:
            label = " ".join("".join(self._current_anchor).split())
            self.anchor_labels.append(label)
            self.anchor_destinations.append((label, self._current_href))
            self._current_anchor = None
            self._current_href = None

    def handle_data(self, data):
        self.text_chunks.append(data)
        if self._current_anchor is not None:
            self._current_anchor.append(data)


def _markup_display_witness(internal: bytes, rendered_plain: bytes,
                            rendered_html: bytes | None) -> dict:
    """Compare exact source headings to copied GUI text and count real links."""
    if (not isinstance(internal, bytes) or len(internal) > 256_000
            or not isinstance(rendered_plain, bytes) or len(rendered_plain) > 256_000
            or (rendered_html is not None and
                (not isinstance(rendered_html, bytes) or len(rendered_html) > 256_000))):
        raise PilotError("Unbounded private Xiphos markup witness")
    original = internal.decode("utf-8", errors="replace")
    copied = rendered_plain.decode("utf-8", errors="replace")
    extracted_titles = []
    for value in _TITLE_TAG.findall(original)[:32]:
        parser = _BoundedMarkupScanner()
        parser.feed(unescape(value))
        title = " ".join("".join(parser.text_chunks).split())
        if len(title) >= 8:
            extracted_titles.append(title)
    visible = " ".join(copied.split())
    exact_titles = sum(1 for value in extracted_titles if value in visible)
    rich_link_count = 0
    actual_anchor_labels = set()
    actual_anchor_destinations = []
    actual_html_text = ""
    if rendered_html:
        parser = _BoundedMarkupScanner()
        parser.feed(rendered_html.decode("utf-8", errors="replace"))
        rich_link_count = min(parser.link_count, 5000)
        actual_anchor_labels = set(parser.anchor_labels)
        actual_anchor_destinations = parser.anchor_destinations
        actual_html_text = " ".join("".join(parser.text_chunks).split())
    source_reference_labels = []
    for value in _REFERENCE_WITH_LABEL.findall(original)[:256]:
        parser = _BoundedMarkupScanner()
        parser.feed(unescape(value))
        label = " ".join("".join(parser.text_chunks).split())
        if len(label) >= 5:
            source_reference_labels.append(label)
    # A semantic match only proves the *original hyperlink label* was copied
    # as an actual HTML anchor; its OSIS target and click navigation are not
    # independently verified by the clipboard.
    matched_anchor_labels = sum(
        1 for label in source_reference_labels if label in actual_anchor_labels
    )
    exact_source_target_hrefs = 0
    for attrs, raw_label in _REFERENCE_WITH_ATTRIBUTES.findall(original)[:256]:
        osis = _OSIS_REF_ATTRIBUTE.search(attrs)
        if not osis:
            continue
        raw_target = unescape(osis.group(2)).strip()
        if raw_target.startswith("Bible:"):
            raw_target = raw_target[len("Bible:"):]
        if not 3 <= len(raw_target) <= 160:
            continue
        parser = _BoundedMarkupScanner()
        parser.feed(unescape(raw_label))
        label = " ".join("".join(parser.text_chunks).split())
        if len(label) < 5:
            continue
        for rendered_label, href in actual_anchor_destinations:
            uri = unquote(unescape(href)).casefold()
            if (rendered_label == label and re.search(
                r"(?<![a-z0-9])" + re.escape(raw_target.casefold()) + r"(?![a-z0-9])",
                uri,
            )):
                exact_source_target_hrefs += 1
                break
    return {
        "original_internal_title_elements_found": len(extracted_titles),
        "exact_original_titles_in_copied_gui_text": exact_titles,
        "exact_original_titles_in_copied_gui_rich_html": sum(
            1 for value in extracted_titles if value in actual_html_text
        ),
        "original_internal_reference_elements_found": min(
            len(_REFERENCE_TAG.findall(original)), 5000
        ),
        "original_stock_nontrivial_reference_labels_found": len(source_reference_labels),
        "source_reference_labels_observed_as_real_gui_HTML_anchors":
            matched_anchor_labels,
        "exact_native_source_osisref_encoded_in_real_gui_HTML_link_destinations":
            exact_source_target_hrefs,
        "real_gui_rich_html_selection_available": bool(rendered_html),
        "real_gui_rich_html_anchor_elements_found": rich_link_count,
        "xiphos_link_click_target_and_navigation_verified": False,
    }


def _optional_real_rich_xiphos_selection(env: dict) -> bytes | None:
    """Read HTML offered by the real clipboard, never synthesize markup."""
    try:
        targets = _x11(
            ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
            env, timeout=6,
        )
        if "text/html" not in targets.decode("ascii", errors="ignore").splitlines():
            return None
        return _x11(
            ["xclip", "-selection", "clipboard", "-t", "text/html", "-o"],
            env, timeout=7,
        )
    except PilotError:
        return None


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


def _seed_x11_clipboard(env: dict) -> None:
    """Set an unmistakably unrelated private sentinel before each GUI copy.

    Xclip's background selection owner must not inherit a captured stdout
    pipe from subprocess.run, which can otherwise block until its lifetime
    ends. An empty input also need not yield a valid X11 selection.
    """
    try:
        outcome = subprocess.run(
            ["xclip", "-selection", "clipboard", "-i"],
            input=b"XIPHOS_PRIVATE_CLIPBOARD_SENTINEL_NOT_SOURCE_TEXT",
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PilotError("Cannot reset private Xiphos GUI clipboard") from exc
    if outcome.returncode != 0:
        raise PilotError("Refusing stale original commentary X11 selection")


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


def _commentary_pane_focus_points(env: dict, window: str) -> tuple[tuple[int,int], ...]:
    """Only the commentary side of a *real, validated* Xiphos main window.

    Source: Xiphos manual's commentary pane is on the right; its actual main
    window is checked above. Coordinates are proportional to the window
    geometry on our private 1280x800 Xvfb, never used on a user's desktop.
    A click is an observation attempt, NOT proof that text was rendered.
    """
    geometry = _x11(
        ["xdotool", "getwindowgeometry", "--shell", window], env,
    ).decode("ascii", errors="ignore")
    dims = dict(re.findall(r"^(X|Y|WIDTH|HEIGHT)=(-?\d+)$", geometry, re.M))
    if set(dims) != {"X", "Y", "WIDTH", "HEIGHT"}:
        raise PilotError("Unknown Xiphos main-reader geometry")
    x, y, width, height = [int(dims[k]) for k in ("X", "Y", "WIDTH", "HEIGHT")]
    if (x < 0 or y < 0 or width < 700 or width > 1280
            or height < 500 or height > 800 or x + width > 1280
            or y + height > 800):
        raise PilotError("Xiphos commentary pane outside reviewed X11 screen")
    return (
        (x + width * 85 // 100, y + height * 38 // 100),
        (x + width * 83 // 100, y + height * 57 // 100),
    )


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
                "bounded_xiphos_ui_failed_action_by_passage": {
                    key: "main_window_not_found" for key in comparisons
                },
                "copied_gui_clipboard_byte_count_by_passage": {
                    key: 0 for key in comparisons
                },
                "bounded_right_commentary_pane_focus_attempts_by_passage": {
                    key: 0 for key in comparisons
                },
                "real_markup_rendering_observation_by_passage": {
                    key: _markup_display_witness(
                        item.get("commentary_internal", b""), b"", None
                    ) for key, item in comparisons.items()
                },
                "independent_gui_commentary_excerpt_match_count": 0}
    result = {}
    failures = {}
    copied_sizes = {}
    focus_attempts = {}
    markup_by_passage = {}
    accepted = True
    try:
        right_side_points = _commentary_pane_focus_points(env, window)
    except PilotError:
        right_side_points = ()
    for ref, originals in comparisons.items():
        stage = "focus_main_window"
        try:
            _x11(["xdotool", "windowfocus", "--sync", window], env)
            for action, command in (
                ("select_reference", ["xdotool", "key", "--clearmodifiers", "ctrl+l"]),
                ("enter_reference", ["xdotool", "type", "--clearmodifiers", "--delay", "25", ref]),
                ("open_reference", ["xdotool", "key", "Return"]),
                ("raise_commentary_pane", ["xdotool", "key", "--clearmodifiers", "alt+c"]),
            ):
                stage = action
                _x11(command, env)
            time.sleep(2)
            focus_attempts[ref] = 0
            result[ref] = False
            copied_sizes[ref] = 0
            markup_by_passage[ref] = _markup_display_witness(
                originals.get("commentary_internal", b""), b"", None
            )
            for px, py in right_side_points:
                stage = "focus_right_hand_commentary_pane"
                _x11(
                    # Do not use --sync here: the same coordinate can be
                    # revisited on another verse, and xdotool's wait-for-motion
                    # may then time out because no new pointer movement occurs.
                    ["xdotool", "mousemove", str(px), str(py), "click", "1"],
                    env,
                )
                focus_attempts[ref] += 1
                time.sleep(0.7)
                # Seed a non-authorial sentinel. If the GUI doesn't replace
                # it, it cannot accidentally match original commentary.
                stage = "clear_prior_clipboard"
                _seed_x11_clipboard(env)
                stage = "select_commentary_text"
                _x11(["xdotool", "key", "--clearmodifiers", "ctrl+a"], env)
                stage = "copy_commentary_text"
                _x11(["xdotool", "key", "--clearmodifiers", "ctrl+c"], env)
                time.sleep(1)
                stage = "read_commentary_clipboard"
                selected = _x11(["xclip", "-selection", "clipboard", "-o"], env)
                copied_sizes[ref] = len(selected)
                result[ref] = _long_commentary_excerpt_is_on_gui_clipboard(
                    originals["commentary"], originals["bible"], selected
                )
                markup_by_passage[ref] = _markup_display_witness(
                    originals.get("commentary_internal", b""),
                    selected, _optional_real_rich_xiphos_selection(env),
                )
                if result[ref]:
                    break
        except PilotError:
            accepted = False
            failures[ref] = stage
            copied_sizes[ref] = 0
            focus_attempts.setdefault(ref, 0)
            markup_by_passage.setdefault(ref, _markup_display_witness(
                originals.get("commentary_internal", b""), b"", None
            ))
            result[ref] = False
    return {
        "real_main_reader_window_found": True,
        "actual_passage_commands_accepted": accepted,
        "commentary_clipboard_match_by_passage": result,
        "bounded_xiphos_ui_failed_action_by_passage": failures,
        "copied_gui_clipboard_byte_count_by_passage": copied_sizes,
        "bounded_right_commentary_pane_focus_attempts_by_passage": focus_attempts,
        "real_markup_rendering_observation_by_passage": markup_by_passage,
        "independent_gui_commentary_excerpt_match_count": sum(result.values()),
    }


def _attempt_actual_context_heading_menu(env: dict, comparisons: dict) -> dict:
    """Optional real Gtk/AT-SPI check of Xiphos's documented intro menu.

    Real Gtk menu activation is required; right-click coordinates alone or
    untrusted screenshot/clipboard differences cannot count as menu success.
    This detects a *reader feature*, not original source heading parity:
    Xiphos's 'Display Chapter Heading' navigates to a separate SWORD
    chapter-introduction key (0), rather than proving the verse's <title>
    tag was rendered with the correct typography.
    """
    result = {
        "real_xiphos_commentary_chapter_heading_menu_activated": False,
        "actual_commentary_pane_content_changed_after_heading_action": False,
        "chapter_heading_text_matches_original_native_intro": False,
        "all_in_verse_original_title_elements_rendered_as_visual_headings": False,
        "reader_gui_heading_css_typography_approved": False,
    }
    if (env.get("BIBLE_PRIVATE_GUI_A11Y") != "1"
            or not env.get("DBUS_SESSION_BUS_ADDRESS")
            or not Path("/usr/bin/python3").is_file()
            or not comparisons):
        return result
    window = _main_xiphos_window(env)
    if window is None:
        return result
    try:
        point = _commentary_pane_focus_points(env, window)[0]
        ref = next(iter(comparisons))
        item = comparisons[ref]
        _x11(["xdotool", "windowfocus", "--sync", window], env)
        for command in (
            ["xdotool", "key", "--clearmodifiers", "ctrl+l"],
            ["xdotool", "type", "--clearmodifiers", "--delay", "25", ref],
            ["xdotool", "key", "Return"],
            ["xdotool", "key", "--clearmodifiers", "alt+c"],
        ):
            _x11(command, env)
        time.sleep(1)
        px, py = point

        def copy_actual_commentary():
            _x11(["xdotool", "mousemove", str(px), str(py), "click", "1"], env)
            _seed_x11_clipboard(env)
            _x11(["xdotool", "key", "--clearmodifiers", "ctrl+a"], env)
            _x11(["xdotool", "key", "--clearmodifiers", "ctrl+c"], env)
            time.sleep(0.5)
            return _x11(["xclip", "-selection", "clipboard", "-o"], env)

        original_plain = copy_actual_commentary()
        if not _long_commentary_excerpt_is_on_gui_clipboard(
            item["commentary"], item["bible"], original_plain
        ):
            return result
        # One real menu popover on the private Xvfb, then activate exactly the
        # *accessible menu item name* through Gtk/AT-SPI, not a guessed pixel.
        _x11(["xdotool", "mousemove", str(px), str(py), "click", "3"], env)
        time.sleep(0.5)
        helper = ROOT / "scripts" / "commentary_xiphos_a11y_menu.py"
        if helper.is_symlink() or not helper.is_file():
            raise PilotError("Reviewed Xiphos accessibility helper missing")
        activated = subprocess.run(
            ["/usr/bin/python3", str(helper), "chapter"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, check=False,
        )
        if activated.returncode != 0 or activated.stdout != b"ACTIVATED\n":
            _x11(["xdotool", "key", "Escape"], env)
            return result
        result["real_xiphos_commentary_chapter_heading_menu_activated"] = True
        time.sleep(0.7)
        changed = copy_actual_commentary()
        result["actual_commentary_pane_content_changed_after_heading_action"] = (
            changed != original_plain and len(changed) > 20
            and changed not in (b"private-xiphos-sentinel",)
        )
        return result
    except (PilotError, OSError, subprocess.TimeoutExpired):
        return result


def _run_real_gui(root: Path, comparisons: dict[str, dict], *, seconds: int,
                  commentary_module_id: str = "MHCC") -> dict:
    if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", commentary_module_id)
            or not 6 <= seconds <= 25 or root.is_symlink() or not root.is_dir()
            or not (root / "mods.d" / (commentary_module_id.lower()+".conf")).is_file()
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
    optional_a11y = os.environ.get("BIBLE_PRIVATE_GUI_A11Y") == "1"
    if optional_a11y:
        if not env.get("DBUS_SESSION_BUS_ADDRESS"):
            raise PilotError("Real Xiphos accessibility menu requires one shared private DBus session")
        env.pop("NO_AT_BRIDGE", None)
        env["BIBLE_PRIVATE_GUI_A11Y"] = "1"
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
            (["xiphos"] if optional_a11y else
             ["dbus-run-session", "--", "xiphos"]), env=env,
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
        heading_menu = _attempt_actual_context_heading_menu(env, comparisons)
        return {
            "real_xiphos_executable_started_and_visible": True,
            "actual_Xiphos_heading_context_menu_observation": heading_menu,
            "original_source_SWORD_PATH_isolated": True,
            **inspection,
        }
    finally:
        if app is not None:
            _stop_group(app)
        if display is not None:
            _stop_group(display)


def prepare_original_and_candidate_gui_samples(
    manifest: dict, *, original_root: Path, reader_root: Path,
    selected_module_id: str, source_reference_cases: dict,
    native_raw_key_binary: Path,
) -> tuple[dict, list[str], list[str], list[str]]:
    """Use the same five original key specimens for upstream or relabelled stock.

    The original and selected compiled module text is independently compared
    for every candidate key. A different empty verse is never silently added.
    The actual raw OSIS title/link markup ALWAYS comes from original CrossWire,
    not a synthesized title or editable clone.
    """
    original_id = manifest["module_id"]
    if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", selected_module_id)
            or not original_root.is_dir() or not reader_root.is_dir()):
        raise PilotError("Unsafe commentary module comparison roots")

    def read_pair(passage: str):
        old_code, stock = query(
            original_id, passage, fmt="plain", root=original_root,
            exe="diatheke", limit=256 * 1024, timeout=30,
        )
        new_code, selected = query(
            selected_module_id, passage, fmt="plain", root=reader_root,
            exe="diatheke", limit=256 * 1024, timeout=30,
        )
        if (old_code != 0 or new_code != 0
                or not present_key(passage, stock, old_code)
                or not present_key(passage, selected, new_code)
                or len(stock) <= 64 or len(selected) <= 64):
            return None
        if original_id != selected_module_id:
            _reader_identity_only_equivalence(
                stock, selected,
                old_id=original_id, candidate_id=selected_module_id,
            )
        elif stock != selected:
            raise PilotError(
                "Original reader output differs from actual selected stock bytes"
            )
        code, bible = query(
            BIBLE_MODULE, passage, fmt="plain", root=reader_root,
            exe="diatheke", limit=256 * 1024, timeout=30,
        )
        if code != 0 or not present_key(passage, bible, code) or len(bible) <= 16:
            raise PilotError(
                "Reviewed Bible could not navigate actual occupied commentary key"
            )
        return {
            "commentary": selected,
            "bible": bible,
            "commentary_internal": _exact_native_commentary_raw(
                original_root, original_id, passage, native_raw_key_binary
            ),
        }

    comparisons = {}
    sparse_original_commentary_slots = []
    for ref in _candidate_passages(manifest):
        item = read_pair(ref)
        if item is None:
            sparse_original_commentary_slots.append(ref)
            continue
        comparisons[ref] = item
        if len(comparisons) == MAX_SUBSTANTIVE_SAMPLES:
            break
    if len(comparisons) != MAX_SUBSTANTIVE_SAMPLES:
        raise PilotError("Not enough distinct nonempty original source commentary anchors")
    baseline = list(comparisons)
    link_samples = []
    for ref in source_reference_cases["real_reference_bearing_original_native_samples"]:
        if ref in comparisons:
            continue
        item = read_pair(ref)
        if item is None:
            continue
        comparisons[ref] = item
        link_samples.append(ref)
        if len(link_samples) == 2:
            break
    if len(link_samples) != 2:
        raise PilotError("Not enough actual original scripture-link-bearing keys")
    return comparisons, baseline, link_samples, sparse_original_commentary_slots


def observe_dual_module_reader(resource_id: str = "mhcc-crosswire",
                               *, native_raw_key_binary: Path,
                               native_raw_corpus_binary: Path,
                               seconds: int = 12) -> dict:
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
        source_reference_cases = _original_stock_reference_bearing_samples(
            installed, manifest["module_id"], native_raw_corpus_binary,
            expected_corpus_sha256=manifest["native_raw_corpus_sha256"],
        )
        comparisons, baseline, link_samples, sparse_original_commentary_slots = (
            prepare_original_and_candidate_gui_samples(
                manifest, original_root=installed, reader_root=installed,
                selected_module_id=manifest["module_id"],
                source_reference_cases=source_reference_cases,
                native_raw_key_binary=native_raw_key_binary,
            )
        )
        observed = _run_real_gui(installed, comparisons, seconds=seconds)
        return {
            "schema_version": 1,
            "status": "pinned_original_MHCC_plus_attested_Bible_real_Xiphos_reader_probe",
            "resource_id": resource_id,
            "exact_original_commentary_zip_sha256": obtained["sha256"],
            "exact_original_commentary_conf_sha256": sha256(metadata).hexdigest(),
            "original_module_id": manifest["module_id"],
            "installed_reviewed_bible": bible,
            "authentic_original_reference_bearing_inventory": source_reference_cases,
            "both_real_sword_modules_have_nonempty_diatheke_readback": True,
            "sample_count": len(comparisons),
            "original_baseline_commentary_text_gui_probe_references": baseline,
            "genuine_original_reference_bearing_gui_probe_references": link_samples,
            "actual_substantive_sample_references": list(comparisons),
            "original_sparse_commentary_slots_skipped": sparse_original_commentary_slots,
            "unoccupied_stock_verses_silently_reintroduced": False,
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
    p.add_argument("--native-raw-key-binary", type=Path, required=True)
    p.add_argument("--native-raw-corpus-binary", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        raise PilotError("Unsafe or preexisting Xiphos receipt path")
    result = observe_dual_module_reader(
        args.resource_id,
        native_raw_key_binary=args.native_raw_key_binary,
        native_raw_corpus_binary=args.native_raw_corpus_binary,
        seconds=args.seconds,
    )
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("Original MHCC and reviewed Bible tested in real isolated Xiphos; no source prose/screenshots exported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
