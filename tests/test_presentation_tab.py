"""(0.479) The ArqSynth Presentation tab without a window (Qt off screen): its tab among the views' — always the last,
not closed, not dragged, not saved with the project, never chosen by itself when the tab beside it closes —, its
glyphs, the Presentation's lens as pygfx's and back."""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("ARQBIM_CACHE_DIR", os.path.join(os.environ.get("TEMP", "/tmp"), "arqbim_test_cache"))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from arqbim.ui import presentation_glyphs, presentation_mode, view_tabs  # noqa: E402

PLAN = ("plan", "piso0")
SECTION = ("section", "Corte 1")
CAMERA = {"position": (1.0, 2.0, 3.0), "rotation": (0.0, 0.0, 0.0, 1.0), "focus": (0.0, 0.0, 0.0), "fov": 45.0,
          "width": 16.0, "height": 9.0, "zoom": 1.0}


def tearDownModule():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete.value)


class Tabs(unittest.TestCase):
    def setUp(self):
        self.bar = QtWidgets.QTabBar()
        self.shown = []
        icon = lambda: presentation_glyphs.icon("scene", "#2f6fe4", 16)    # noqa: E731
        self.tabs = view_tabs.ViewTabs(self.bar, self.shown.append, lambda key: "/".join(key),
                                       lambda: dict(CAMERA), lambda state: None,
                                       home_icon=icon, present_icon=icon)

    def test_last_and_fixed(self):
        tabs, bar = self.tabs, self.bar
        tabs.open(view_tabs.THREE_D)
        self.assertEqual(tabs.keys, [view_tabs.START, view_tabs.THREE_D, view_tabs.PRESENT])
        tabs.open(PLAN)
        tabs.open(SECTION)
        self.assertEqual(tabs.keys[-1], view_tabs.PRESENT)              # (new tabs before it)
        self.assertEqual(tabs.keys.index(SECTION), 3)
        k = tabs.keys.index(view_tabs.PRESENT)
        self.assertIsNone(bar.tabButton(k, QtWidgets.QTabBar.ButtonPosition.RightSide))     # (no ×)
        tabs.close(k)
        self.assertIn(view_tabs.PRESENT, tabs.keys)                     # (not closed)
        tabs.open(view_tabs.PRESENT)
        self.assertEqual(tabs.current(), view_tabs.PRESENT)
        self.assertEqual(self.shown[-1], view_tabs.PRESENT)
        tabs.open(("elevation", "S"))                                     # (opened from it: before it)
        self.assertEqual(tabs.keys[-2:], [("elevation", "S"), view_tabs.PRESENT])
        bar.moveTab(len(tabs.keys) - 1, 1)                                # (dragged away…)
        tabs._pin()                                                       # (…and let go: back to the end)
        self.assertEqual(tabs.keys[0], view_tabs.START)
        self.assertEqual(tabs.keys[-1], view_tabs.PRESENT)
        self.assertNotIn("presentation", tabs.text())
        self.assertNotIn(view_tabs.PRESENT, tabs.models())
        self.assertNotIn(["presentation"], [tab["key"] for tab in tabs.state()["tabs"]])

    def test_closing_beside_it(self):
        """The view just before it closed while shown: the one on its left comes, not the Presentation's."""
        tabs = self.tabs
        tabs.open(view_tabs.THREE_D)
        tabs.open(PLAN)
        self.assertEqual(tabs.current(), PLAN)
        tabs.close(tabs.keys.index(PLAN))
        self.assertEqual(tabs.current(), view_tabs.THREE_D)
        self.assertEqual(self.shown[-1], view_tabs.THREE_D)

    def test_ctrl_tab_and_state(self):
        tabs = self.tabs
        tabs.open(view_tabs.THREE_D)
        tabs.open(PLAN)
        tabs.step(1)
        self.assertEqual(tabs.current(), view_tabs.THREE_D)              # (round the views: not the fixed tabs)
        tabs.open(view_tabs.PRESENT)
        self.assertIsNone(tabs.state()["current"])                        # (not the project's)
        tabs.restore({"tabs": [{"key": ["3d"], "camera": None}, {"key": list(PLAN), "camera": None}],
                      "current": list(PLAN)}, lambda key: True)
        self.assertEqual(tabs.keys, [view_tabs.START, view_tabs.THREE_D, PLAN, view_tabs.PRESENT])
        tabs.reset()
        self.assertEqual(tabs.keys, [view_tabs.START, view_tabs.THREE_D, view_tabs.PRESENT])

    def test_without_it(self):
        """A bar without the Presentation's icon has no such tab (as before)."""
        bar = QtWidgets.QTabBar()
        tabs = view_tabs.ViewTabs(bar, lambda key: None, lambda key: "x", lambda: {}, lambda state: None)
        tabs.open(view_tabs.THREE_D)
        self.assertNotIn(view_tabs.PRESENT, tabs.keys)


class Glyphs(unittest.TestCase):
    def test_every_glyph_drawn(self):
        for kind in presentation_glyphs.KINDS:
            image = presentation_glyphs.pixmap(kind, "#202020", 18).toImage()
            inked = sum(1 for x in range(image.width()) for y in range(image.height())
                        if QtGui.QColor(image.pixelColor(x, y)).alpha() > 40)
            self.assertGreater(inked, 20, kind)
        on = presentation_glyphs.icon("eye", "#202020", 16, on_colour="#ffffff")
        self.assertFalse(on.pixmap(16, 16, QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On).isNull())


class Lens(unittest.TestCase):
    def test_fov_both_ways(self):
        for vertical in (20.0, 35.0, 50.0, 65.0):
            for aspect in (1.0, 16 / 9, 2.4):
                there = presentation_mode.pygfx_fov(vertical, aspect)
                self.assertAlmostEqual(presentation_mode.vertical_fov(there, aspect), vertical, places=6)
        self.assertEqual(presentation_mode.vertical_fov(0.0, 1.5), 0.0)
        # (a square view: pygfx's is the vertical one)
        self.assertAlmostEqual(presentation_mode.pygfx_fov(35.0, 1.0), 35.0, places=9)
        self.assertTrue(math.isfinite(presentation_mode.pygfx_fov(65.0, 3.0)))


if __name__ == "__main__":
    unittest.main()
