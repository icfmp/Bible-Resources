"""Synthetic fail-closed tests for isolated Xiphos startup of stock zCom commentary."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from commentary_stock_xiphos_smoke import _probe_real_gui
from pilot_preflight import PilotError


class OriginalStockXiphosSmokeTests(unittest.TestCase):
    def make_root(self, parent):
        root = Path(parent) / "installed"
        (root / "mods.d").mkdir(parents=True)
        return root

    @patch("commentary_stock_xiphos_smoke._stop_group")
    @patch("commentary_stock_xiphos_smoke._visible_window", return_value=True)
    @patch("commentary_stock_xiphos_smoke.time.sleep")
    @patch("commentary_stock_xiphos_smoke.shutil.which", return_value="/usr/bin/fake")
    @patch("commentary_stock_xiphos_smoke.subprocess.Popen")
    def test_genuine_gui_window_observation_does_not_claim_rendered_commentary(
        self, popen, _which, _sleep, window, stop,
    ):
        display = MagicMock()
        display.poll.return_value = None
        app = MagicMock()
        app.poll.return_value = None
        popen.side_effect = [display, app]
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            report = _probe_real_gui(root, seconds=6)
            self.assertTrue(report["real_xiphos_X11_window_found"])
            self.assertTrue(report["isolated_original_SWORD_PATH"])
            self.assertFalse(report["independent_commentary_text_actually_rendered_and_read"])
            self.assertFalse(report["AndBible_Android_GUI_tested"])
            self.assertFalse(report["screenshot_or_original_commentary_text_uploaded"])
        self.assertEqual(stop.call_count, 2)
        self.assertTrue(window.called)
        env = popen.call_args_list[1].kwargs["env"]
        self.assertEqual(env["SWORD_PATH"], str(root))
        self.assertEqual(env["DISPLAY"], ":91")
        self.assertNotEqual(env["HOME"], str(Path.home()))

    @patch("commentary_stock_xiphos_smoke._stop_group")
    @patch("commentary_stock_xiphos_smoke._visible_window", return_value=False)
    @patch("commentary_stock_xiphos_smoke.time.sleep")
    @patch("commentary_stock_xiphos_smoke.shutil.which", return_value="/usr/bin/fake")
    @patch("commentary_stock_xiphos_smoke.subprocess.Popen")
    def test_no_visible_xiphos_window_fails_and_processes_are_stopped(
        self, popen, _which, _sleep, _window, stop,
    ):
        display, app = MagicMock(), MagicMock()
        display.poll.return_value = None
        app.poll.return_value = None
        popen.side_effect = [display, app]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PilotError, "visible"):
                _probe_real_gui(self.make_root(tmp), seconds=6)
        self.assertEqual(stop.call_count, 2)

    @patch("commentary_stock_xiphos_smoke._stop_group")
    @patch("commentary_stock_xiphos_smoke.time.sleep")
    @patch("commentary_stock_xiphos_smoke.shutil.which", return_value="/usr/bin/fake")
    @patch("commentary_stock_xiphos_smoke.subprocess.Popen")
    def test_early_window_manager_exit_is_not_success(
        self, popen, _which, _sleep, stop,
    ):
        display = MagicMock()
        display.poll.side_effect = [None, 1]
        app = MagicMock()
        app.poll.return_value = None
        popen.side_effect = [display, app]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PilotError, "prematurely"):
                _probe_real_gui(self.make_root(tmp), seconds=6)
        self.assertEqual(stop.call_count, 2)

    def test_reject_short_run_or_missing_real_module_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            with self.assertRaisesRegex(PilotError, "Unsafe"):
                _probe_real_gui(root, seconds=2)
            with self.assertRaisesRegex(PilotError, "Unsafe"):
                _probe_real_gui(Path(tmp) / "does-not-exist", seconds=6)

    @patch("commentary_stock_xiphos_smoke.shutil.which", return_value=None)
    def test_refuse_missing_independent_gui_tool(self, _which):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PilotError, "missing"):
                _probe_real_gui(self.make_root(tmp), seconds=6)


if __name__ == "__main__":
    unittest.main()
