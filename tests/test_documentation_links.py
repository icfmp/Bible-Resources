"""Guard local links after documentation reorganization.

This checks local Markdown targets, not the correctness of external URLs or the
validity of editorial evidence. It does not read copyrighted source payloads.
"""
from __future__ import annotations

from pathlib import Path
from hashlib import sha1
import json
import re
import subprocess
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"(?ms)^\s*```[^\n]*\n.*?^\s*```\s*$")
SKIP = ("http:", "https:", "mailto:", "data:", "#", "//")


class DocumentationLinkIntegrityTests(unittest.TestCase):
    def test_existing_local_markdown_destinations(self):
        tracked = subprocess.run(
            ["git", "ls-files", "-z", "--", "docs", "sources/cleaned", "history"],
            cwd=ROOT, check=True, capture_output=True, timeout=20,
        ).stdout.split(b"\0")
        # A separately approved reader profile has an immutable, signed Git
        # blob. Its old relative historical links cannot be rewritten without
        # invalidating that editorial approval. Verify its exact signed bytes
        # before exempting it from current relative-link navigation checks.
        pinned = set()
        for receipt_file in ROOT.glob("modules/*/profiles/*.json"):
            receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
            target = (ROOT / receipt["source_path"]).resolve()
            self.assertTrue(target.is_file(), str(target))
            raw = target.read_bytes()
            digest = sha1(b"blob " + str(len(raw)).encode() +
                          b"\0" + raw).hexdigest()
            self.assertEqual(digest, receipt["source_git_blob_sha1"])
            pinned.add(target)
        missing = []
        checked = 0
        for raw in tracked:
            if not raw:
                continue
            rel = raw.decode("utf-8")
            source = ROOT / rel
            if source.suffix.lower() != ".md" or not source.is_file():
                continue
            if source.resolve() in pinned:
                continue
            text = FENCE.sub("", source.read_text(encoding="utf-8"))
            for match in LINK.finditer(text):
                url = match.group(1)
                if url.startswith(SKIP):
                    continue
                parsed = urlsplit(url)
                if parsed.scheme or not parsed.path:
                    continue
                dest = (source.parent / unquote(parsed.path)).resolve()
                checked += 1
                if not dest.is_relative_to(ROOT) or not dest.exists():
                    missing.append(f"{rel}: {url}")
        self.assertGreater(checked, 50)
        self.assertFalse(missing, "Broken local Markdown links:\n" +
                         "\n".join(missing[:100]))


if __name__ == "__main__":
    unittest.main()
