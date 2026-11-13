#!/usr/bin/python3
"""Activate exactly one real Xiphos commentary context-menu item via AT-SPI.

Called by the isolated Xvfb/Gtk3 commentary test, on the SAME private D-Bus
session as real Xiphos, only after a genuine right-click in the commentary.
It has NO input corresponding to the source author's text or biblical target.
Only one fixed action is permitted; no arbitrary accessible object names,
clipboard contents, or screenshots leave the runner.

This is a bounded GUI observation tool, not a module heading parity claim.
"""
from __future__ import annotations

import os
import sys
import time

ALLOWED = {
    "chapter": "Display Chapter Heading",
    "book": "Display Book Heading",
}
MAX_NODES = 900
MAX_DEPTH = 13


def _norm(s):
    return " ".join(str(s).replace("_", "").split()).casefold()


def _activate_one(action):
    import pyatspi
    desktop = pyatspi.Registry.getDesktop(0)
    apps = []
    for i in range(min(desktop.childCount, 100)):
        try:
            app = desktop.getChildAtIndex(i)
            if _norm(app.name) == "xiphos":
                apps.append(app)
        except (RuntimeError, AttributeError):
            continue
    if len(apps) != 1:
        return False
    target = _norm(ALLOWED[action])
    scanned = 0
    stack = [(apps[0], 0)]
    while stack and scanned < MAX_NODES:
        obj, depth = stack.pop()
        scanned += 1
        try:
            role = _norm(obj.getRoleName())
            if role in {"menu item", "check menu item"} and _norm(obj.name) == target:
                state = obj.getState()
                if (not state.contains(pyatspi.STATE_VISIBLE)
                        or not state.contains(pyatspi.STATE_SHOWING)):
                    continue
                actions = obj.queryAction()
                if actions.nActions != 1:
                    continue
                return bool(actions.doAction(0))
            if depth < MAX_DEPTH:
                count = min(obj.childCount, 100)
                for n in range(count - 1, -1, -1):
                    stack.append((obj.getChildAtIndex(n), depth + 1))
        except (RuntimeError, AttributeError):
            continue
    return False


def main():
    if (len(sys.argv) != 2 or sys.argv[1] not in ALLOWED
            or os.environ.get("DISPLAY") != ":91"
            or os.environ.get("BIBLE_PRIVATE_GUI_A11Y") != "1"
            or not os.environ.get("DBUS_SESSION_BUS_ADDRESS")
            or not os.environ.get("SWORD_PATH")):
        return 2
    for _ in range(8):
        try:
            if _activate_one(sys.argv[1]):
                print("ACTIVATED")
                return 0
        except (ImportError, RuntimeError, AttributeError):
            break
        time.sleep(0.25)
    print("NOT_FOUND")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
