"""Messwerte und Mausgesten prüfen, ohne FEMM oder Tkinter zu starten."""
import unittest
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import NavigationToolbar2, MouseEvent
from matplotlib.tri import Triangulation
from field_measurements import FieldSampler, FieldMeasurements
from plot_navigation import FieldNavigation


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set(xlim=(-1, 11), ylim=(-1, 11))
        self.toolbar = NavigationToolbar2(self.canvas)
        self.nav = FieldNavigation(self.canvas, self.toolbar)
        self.nav.reset(self.ax, (-1, 11, -1, 11))
        tri = Triangulation([0, 10, 0, 10], [0, 0, 10, 10], [[0, 1, 2], [1, 3, 2]])
        self.sampler = FieldSampler(tri, np.array([.01, .2]))
        self.tool = FieldMeasurements(self.canvas, self.toolbar)
        self.nav.pointer_tool = self.tool
        self.tool.set_field(self.ax, self.sampler, "A")
        self.tool.set_enabled(True)
        self.canvas.draw()

    def event(self, name, x=2, z=2, **kwargs):
        px, py = self.ax.transData.transform((x, z))
        event = MouseEvent(name, self.canvas, px, py, **kwargs)
        self.canvas.callbacks.process(name, event)
        return event

    def click(self, x=2, z=2):
        self.event("button_press_event", x, z, button=1)
        self.event("button_release_event", x, z, button=1)
        self.canvas.draw()

    def test_values_are_original_element_values_and_outside_has_no_value(self):
        self.assertEqual(self.sampler.at(2, 2), .01)
        self.assertEqual(self.sampler.at(8, 8), .2)
        for x, z in [(-1, 3), (30, 2), (float("nan"), 2), (2, float("inf")), (None, 2)]:
            self.assertIsNone(self.sampler.at(x, z))
        zero = FieldSampler(Triangulation([0, 1, 0], [0, 0, 1], [[0, 1, 2]]), [0])
        self.assertEqual(zero.at(.2, .2), 0)

    def test_multiple_click_points_and_click_again_removes_only_that_point(self):
        self.click();self.click(8, 8)
        self.assertEqual([p.value for p in self.tool.points], [.01, .2])
        self.assertEqual([p.number for p in self.tool.points], [1, 2])
        self.click()
        self.assertEqual([p.number for p in self.tool.points], [2])
        self.assertIsNone(self.nav.drag)

    def test_drag_changes_position_and_value_without_panning_or_deleting(self):
        self.click();point = self.tool.points[0]
        before = self.ax.get_xlim(), self.ax.get_ylim()
        self.event("button_press_event", button=1)
        self.event("motion_notify_event", 8, 8, button=1)
        self.event("button_release_event", 8, 8, button=1)
        self.assertEqual(len(self.tool.points), 1)
        self.assertAlmostEqual(point.x, 8);self.assertAlmostEqual(point.z, 8)
        self.assertEqual(point.value, .2)
        self.assertIn("0,2 T", point.label.get_text())
        self.assertEqual(before, (self.ax.get_xlim(), self.ax.get_ylim()))
        self.assertIsNone(self.nav.drag)

    def test_mouse_jitter_is_a_click_and_label_can_remove_point(self):
        self.click();self.event("button_press_event", button=1)
        start = self.ax.transData.transform((2, 2))
        event = MouseEvent("motion_notify_event", self.canvas, start[0]+2, start[1]+1, button=1)
        self.canvas.callbacks.process("motion_notify_event", event)
        self.event("button_release_event", button=1)
        self.assertEqual(len(self.tool.points), 0)
        self.click();self.canvas.draw()
        bounds = self.tool.points[0].label.get_bbox_patch().get_window_extent(self.canvas.get_renderer())
        for name in ["button_press_event", "button_release_event"]:
            event = MouseEvent(name, self.canvas, (bounds.x0+bounds.x1)/2, (bounds.y0+bounds.y1)/2, button=1)
            self.canvas.callbacks.process(name, event)
        self.assertEqual(len(self.tool.points), 0)

    def test_fast_second_click_also_removes_without_resetting_view(self):
        self.click();self.nav.zoom(1)
        limits=self.ax.get_xlim(),self.ax.get_ylim()
        self.event("button_press_event",button=1,dblclick=True)
        self.event("button_release_event",button=1)
        self.assertEqual(len(self.tool.points),0)
        self.assertEqual(limits,(self.ax.get_xlim(),self.ax.get_ylim()))

    def test_hover_leaves_no_point_and_hides_outside_or_when_disabled(self):
        self.event("motion_notify_event", 8, 8)
        self.assertTrue(self.tool.hover.get_visible())
        self.assertIn("0,2 T", self.tool.hover.get_text())
        self.assertEqual(len(self.tool.points), 0)
        self.event("motion_notify_event", -0.5, 3)
        self.assertFalse(self.tool.hover.get_visible())
        self.event("motion_notify_event", 8, 8)
        self.tool.set_enabled(False)
        self.assertFalse(self.tool.hover.get_visible())
        self.click()
        self.assertEqual(len(self.tool.points), 0)

    def test_leave_and_release_outside_keep_last_valid_drag_position(self):
        self.click();self.event("button_press_event", button=1)
        self.event("motion_notify_event", 8, 8, button=1)
        self.tool.leave()
        self.assertFalse(self.tool.dragging)
        self.canvas.callbacks.process("button_release_event", MouseEvent("button_release_event", self.canvas, 1, 1, button=1))
        self.assertEqual(len(self.tool.points), 1)
        self.assertEqual(self.tool.points[0].value, .2)

    def test_zoom_redraw_and_switching_cases_keep_each_cases_points(self):
        self.click();self.nav.zoom(1)
        self.assertEqual(self.tool.points[0].value, .01)
        self.figure.clear();self.ax = self.figure.add_subplot(111)
        self.ax.set(xlim=(-1, 11), ylim=(-1, 11))
        self.tool.set_field(self.ax, self.sampler, "B")
        self.assertEqual(len(self.tool.points), 0)
        self.click(8, 8)
        self.tool.set_field(self.ax, self.sampler, "A")
        self.assertEqual([p.value for p in self.tool.points], [.01])
        self.tool.set_field(self.ax, self.sampler, "A")
        self.assertEqual(len(self.tool.points), 1)
        self.tool.set_field(self.ax, self.sampler, "B")
        self.assertEqual([p.value for p in self.tool.points], [.2])
        self.tool.clear()
        self.assertEqual(len(self.tool.points), 0)
        self.tool.set_field(self.ax, self.sampler, "A")
        self.assertEqual(len(self.tool.points), 1)

    def test_export_draws_clones_and_toolbar_modes_yield_to_measurements(self):
        self.click();point = self.tool.points[0]
        other = Figure().add_subplot(111)
        self.tool.draw_saved(other, "A")
        self.assertEqual(len(other.texts), 1)
        self.assertIn("M1", other.texts[0].get_text())
        self.assertIs(point.label.axes, self.ax)
        self.tool.set_enabled(False)
        self.toolbar.pan()
        self.assertTrue(self.toolbar.mode)
        self.tool.set_enabled(True)
        self.assertFalse(self.toolbar.mode)
        self.assertTrue(self.tool.enabled)
        self.event("button_press_event", button=1)
        before = self.ax.get_xlim()
        self.event("scroll_event", step=1)
        self.assertEqual(before, self.ax.get_xlim())


if __name__ == "__main__":unittest.main(verbosity=2)
