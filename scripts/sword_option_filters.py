#!/usr/bin/env python3
"""Reject unregistered SWORD option filters in every repeated .conf declaration.

Canonical registry: https://www.crosswire.org/sword/apiref/swmgr_8cpp_source.html
This is a module-metadata gate, not proof of source/cross-reference rendering.
"""
from __future__ import annotations

from pathlib import Path
import re

# Review against the target stable libSWORD SWMgr registry on engine upgrades.
_BY_SOURCE = {
    "OSIS": frozenset({
        "OSISHeadings", "OSISStrongs", "OSISMorph", "OSISLemma",
        "OSISFootnotes", "OSISScripref", "OSISRedLetterWords",
        "OSISMorphSegmentation", "OSISGlosses", "OSISRuby",
        "OSISXlit", "OSISEnum", "OSISVariants",
    }),
    "ThML": frozenset({
        "ThMLStrongs", "ThMLFootnotes", "ThMLMorph", "ThMLHeadings",
        "ThMLVariants", "ThMLLemma", "ThMLScripref",
    }),
    "GBF": frozenset({
        "GBFStrongs", "GBFFootnotes", "GBFRedLetterWords",
        "GBFMorph", "GBFHeadings",
    }),
}
_COMMON = frozenset({
    "UTF8GreekAccents", "UTF8HebrewPoints", "UTF8ArabicPoints",
    "UTF8Cantillation", "UTF8Transliterator", "GreekLexAttribs", "PapyriPlain",
})
_SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def _registered(value: str, source_type: str | None) -> bool:
    supported = _BY_SOURCE.get(source_type)
    if supported is None:
        return False
    if value in supported | _COMMON:
        return True
    if not (source_type == "OSIS" and value.startswith("OSISReferenceLinks|")):
        return False
    # SWMgr's OSISReferenceLinks filter has six piped fields.
    parts = value.split("|")
    return (len(parts) == 6 and parts[0] == "OSISReferenceLinks"
            and all(parts[i].strip() and len(parts[i]) <= 120
                    for i in (1, 2, 3))
            and len(parts[4]) <= 120
            and parts[5] in {"On", "Off"})


def option_filter_errors(path: Path, source_type: str | None) -> list[str]:
    path = Path(path)
    try:
        if (path.is_symlink() or not path.is_file()
                or path.stat().st_size > 256 * 1024):
            raise ValueError("missing, linked, or oversized conf")
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"{path}: [SWORD_OPTION_FILTER_CONF_INVALID] {exc}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith(("#", ";")) or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key != "GlobalOptionFilter":
            continue
        if not value or len(value) > 800:
            errors.append(
                f"{path}:{line_number}: [SWORD_OPTION_FILTER_MALFORMED]"
            )
            continue
        if value in seen:
            errors.append(
                f"{path}:{line_number}: [SWORD_OPTION_FILTER_DUPLICATE] {value!r}"
            )
        seen.add(value)
        if not _registered(value, source_type):
            name = value.split("|", 1)[0]
            if not _SAFE_NAME.fullmatch(name):
                name = "(invalid-filter-name)"
            errors.append(
                f"{path}:{line_number}: [SWORD_OPTION_FILTER_UNREGISTERED] "
                f"{name!r} is not a registered filter for {source_type!r}"
            )
    return errors
