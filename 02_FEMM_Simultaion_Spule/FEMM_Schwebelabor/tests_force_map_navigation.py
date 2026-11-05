"""Force-map navigation regressions; no FEMM connection is required."""
import unittest
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import NavigationToolbar2, MouseEvent
from force_map_navigation import ForceMapNavigation


class ForceMapNavigationTests(unittest.TestCase):
    def setUp(self):
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasAgg(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.ax.set_xlim(0, 8); self.ax.set_ylim(5, 50); self.ax.set_zlim(0, 3)
        self.ax.view_init(elev=28, azim=-135, roll=0)
        self.ax.set_box_aspect((1.2, 1.05, .85), zoom=1.08)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2(self.canvas)
        self.nav = ForceMapNavigation(self.canvas, self.toolbar)
        self.nav.reset(self.ax)
        self.original = (self.ax.get_xlim(), self.ax.get_ylim(), self.ax.get_zlim())

    def event(self, name, dx=0, dy=0, **kwargs):
        x = self.ax.bbox.x0+self.ax.bbox.width/2+dx
        y = self.ax.bbox.y0+self.ax.bbox.height/2+dy
        return MouseEvent(name, self.canvas, x, y, **kwargs)

    def dispatch(self, event):
        self.canvas.callbacks.process(event.name, event)

    def test_orbit_is_upright_and_limited_at_poles(self):
        self.dispatch(self.event("button_press_event", button=1))
        self.dispatch(self.event("motion_notify_event", dx=60, dy=30, button=1))
        self.assertNotEqual((self.ax.elev, self.ax.azim), (28, -135))
        self.assertEqual(self.ax.roll, 0)
        self.dispatch(self.event("motion_notify_event", dy=2000, button=1))
        self.assertEqual(self.ax.elev, -89)
        self.dispatch(self.event("button_release_event", button=1))
        self.assertIsNone(self.nav.drag)

    def test_wheel_changes_magnification_without_changing_force_ranges(self):
        aspect = self.ax.get_box_aspect().copy()
        self.dispatch(self.event("scroll_event", step=1))
        self.assertTrue(np.all(self.ax.get_box_aspect() > aspect))
        self.assertEqual((self.ax.get_xlim(), self.ax.get_ylim(), self.ax.get_zlim()), self.original)
        self.dispatch(self.event("scroll_event", step=-1))
        np.testing.assert_allclose(self.ax.get_box_aspect(), aspect)
        self.nav.zoom(10000); self.nav.zoom(10000)
        self.assertLessEqual(self.nav.zoom_level, 2.2)

    def test_right_drag_pans_and_double_click_resets_everything(self):
        self.dispatch(self.event("button_press_event", button=3))
        self.dispatch(self.event("motion_notify_event", dx=40, dy=20, button=3))
        self.dispatch(self.event("button_release_event", button=3))
        moved = (self.ax.get_xlim(), self.ax.get_ylim(), self.ax.get_zlim())
        self.assertNotEqual(moved, self.original)
        np.testing.assert_allclose([hi-lo for lo, hi in moved], [8, 45, 3])
        self.nav.zoom(2); self.nav.preset("Draufsicht")
        self.dispatch(self.event("button_press_event", button=1, dblclick=True))
        self.assertEqual((self.ax.get_xlim(), self.ax.get_ylim(), self.ax.get_zlim()), self.original)
        self.assertEqual((self.ax.elev, self.ax.azim, self.ax.roll), (28, -135, 0))
        self.assertEqual(self.nav.zoom_level, 1.08)

    def test_presets_and_refresh_keep_camera_and_relative_pan(self):
        self.nav.preset("Kraft / Strom")
        self.assertEqual((self.ax.elev, self.ax.azim), (0, -90))
        self.nav.zoom(2)
        state = self.nav.snapshot()
        self.figure.clear()
        other = self.figure.add_subplot(111, projection="3d")
        other.set_xlim(0, 10); other.set_ylim(0, 60); other.set_zlim(0, 5)
        self.nav.reset(other, state)
        self.assertEqual((other.elev, other.azim), (0, -90))
        self.assertEqual(self.nav.zoom_level, state["zoom"])
        self.assertEqual(other.get_zlim(), (0, 5))

    def test_colourbar_toolbar_mode_and_old_axes_do_not_receive_gestures(self):
        event = self.event("scroll_event", step=1)
        other = self.figure.add_axes([.9, .1, .03, .6])
        event.inaxes = other
        self.nav.scroll(event)
        self.assertEqual(self.nav.zoom_level, 1.08)
        self.toolbar.pan()
        self.dispatch(self.event("button_press_event", button=1))
        self.assertIsNone(self.nav.drag)
        self.nav.restore_view()
        self.assertFalse(self.toolbar.mode)
        self.nav.reset()
        self.nav.scroll(event)
        self.assertIsNone(self.nav.snapshot())


if __name__ == "__main__": unittest.main()
