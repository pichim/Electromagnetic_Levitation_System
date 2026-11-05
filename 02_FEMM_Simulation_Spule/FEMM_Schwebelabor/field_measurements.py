"""Tesla-Messpunkte auf dem gespeicherten FEMM-Netz, ohne erneuten Solveraufruf."""
from __future__ import annotations

from dataclasses import dataclass
import math
from matplotlib.backend_bases import MouseButton
from matplotlib.backend_tools import Cursors


class FieldSampler:
    """Liest |B| am Mittelpunkt des Netzelements, das den Messort enthält.

    Die CSV enthält einen FEMM-Wert pro Dreieck. Dieser wird unverändert
    verwendet; er ist eine Näherung für den Ort innerhalb des Dreiecks.
    Farbglättung, logarithmische Skala und deren Grenzen sind hier unwirksam.
    """
    def __init__(self, triangulation, magnitudes):
        self.find_triangle = triangulation.get_trifinder()
        self.magnitudes = magnitudes

    def at(self, x, z):
        if x is None or z is None or not math.isfinite(x) or not math.isfinite(z):
            return None
        index = int(self.find_triangle(x, z))
        return None if index < 0 else float(self.magnitudes[index])


def tesla(value):
    return format(value, ".4g").replace(".", ",") + " T"


@dataclass
class Measurement:
    number: int
    x: float
    z: float
    value: float
    marker: object = None
    label: object = None


def position_label(axes, label, x, z):
    """Beschriftung an Rändern nach innen ausrichten, auch nach dem Zoomen."""
    x0, x1 = axes.get_xlim()
    z0, z1 = axes.get_ylim()
    right = x > x0 + .62*(x1-x0)
    below = z > z0 + .80*(z1-z0)
    label.set_position((-10 if right else 10, -10 if below else 10))
    label.set_horizontalalignment("right" if right else "left")
    label.set_verticalalignment("top" if below else "bottom")


def draw_point(axes, point):
    point.marker, = axes.plot([point.x], [point.z], "o", ms=6, mfc="white", mec="#172331",
                              mew=1.4, zorder=30, clip_on=True)
    point.label = axes.annotate(f"M{point.number}: ≈ {tesla(point.value)}", (point.x, point.z),
        xytext=(10, 10), textcoords="offset points", fontsize=8, color="#172331", zorder=31,
        bbox=dict(boxstyle="round,pad=.25", fc="white", ec="#172331", alpha=.96),
        arrowprops=dict(arrowstyle="-", color="#172331", lw=.8), annotation_clip=True)
    point.label.set_clip_on(True)
    position_label(axes, point.label, point.x, point.z)


class FieldMeasurements:
    """Klick: setzen/löschen; Ziehen: verschieben; Fälle behalten eigene Punkte."""
    def __init__(self, canvas, toolbar, changed=None):
        self.canvas, self.toolbar, self.changed = canvas, toolbar, changed
        self.axes = self.sampler = self.case_key = self.hover = self.gesture = None
        self.enabled = False
        self.cases, self.axis_connections = {}, []
        self.connections = [canvas.mpl_connect(name, handler) for name, handler in [
            ("button_press_event", self.press), ("button_release_event", self.release),
            ("motion_notify_event", self.motion), ("figure_leave_event", self.leave),
            ("resize_event", self.layout), ("draw_event", self.layout)]]

    @property
    def points(self):
        return self.cases[self.case_key]["points"] if self.case_key is not None else []

    @property
    def dragging(self):
        return self.gesture is not None

    def notify(self):
        if self.changed is not None:self.changed(self)

    def set_enabled(self, enabled):
        enabled = bool(enabled and self.axes is not None)
        if enabled and self.toolbar.mode:
            name = getattr(self.toolbar.mode, "name", "")
            if name == "PAN":self.toolbar.pan()
            elif name == "ZOOM":self.toolbar.zoom()
        self.enabled = enabled
        self.gesture = None
        self.hide_hover()
        self.canvas.set_cursor(Cursors.SELECT_REGION if enabled else Cursors.POINTER)
        self.notify()
        self.canvas.draw_idle()

    @staticmethod
    def remove_artists(point):
        for artist in (point.marker, point.label):
            if artist is not None:
                try:artist.remove()
                except (ValueError, AttributeError, NotImplementedError):pass
        point.marker = point.label = None

    def set_field(self, axes=None, sampler=None, case_key=None):
        for point in self.points:self.remove_artists(point)
        if self.hover is not None:
            try:self.hover.remove()
            except (ValueError, AttributeError, NotImplementedError):pass
        if self.axes is not None:
            for connection in self.axis_connections:self.axes.callbacks.disconnect(connection)
        self.axis_connections, self.hover, self.gesture = [], None, None
        self.axes, self.sampler, self.case_key = axes, sampler, case_key
        if axes is not None and sampler is not None and case_key is not None:
            self.cases.setdefault(case_key, {"points": [], "next_id": 1})
            for point in self.points:draw_point(axes, point)
            self.hover = axes.annotate("", (0, 0), xytext=(10, 10), textcoords="offset points",
                fontsize=8, color="#172331", zorder=40, annotation_clip=True,
                bbox=dict(boxstyle="round,pad=.3", fc="white", ec="#425564", alpha=.96))
            self.hover.set_clip_on(True)
            self.hover.set_visible(False)
            self.axis_connections = [axes.callbacks.connect(name, self.view_changed)
                                     for name in ("xlim_changed", "ylim_changed")]
            axes.format_coord = self.coordinates
            self.layout()
        else:
            self.enabled = False
            self.canvas.set_cursor(Cursors.POINTER)
        self.notify()

    def coordinates(self, x, z):
        value = self.sampler.at(x, z)
        location = f"x={x:.4g} mm, z={z:.4g} mm"
        return location + (" · |B| ≈ " + tesla(value) if value is not None else " · ausserhalb des FEMM-Netzes")

    def view_changed(self, axes):
        self.hide_hover()
        self.layout()

    def layout(self, event=None):
        if self.axes is not None:
            for point in self.points:
                if point.label is not None:position_label(self.axes, point.label, point.x, point.z)

    def hide_hover(self):
        if self.hover is not None:self.hover.set_visible(False)

    def inside(self, event):
        return (self.axes is not None and self.axes in self.canvas.figure.axes
                and event.inaxes is self.axes and event.xdata is not None and event.ydata is not None)

    def hit(self, event):
        # Erst die tatsächlichen Punkte prüfen, dann ihre Beschriftungen.
        tolerance = 8*self.canvas.figure.dpi/100
        nearby = []
        for point in self.points:
            px, py = self.axes.transData.transform((point.x, point.z))
            distance = math.hypot(px-event.x, py-event.y)
            if distance <= tolerance:nearby.append((distance, point))
        if nearby:return min(nearby, key=lambda item: item[0])[1]
        for point in reversed(self.points):
            if point.label is not None and point.label.contains(event)[0]:return point
        return None

    def press(self, event):
        if not self.enabled or self.toolbar.mode or event.button != MouseButton.LEFT:
            return
        if not self.inside(event):return
        point = self.hit(event)
        if point is None and self.sampler.at(event.xdata, event.ydata) is None:return
        self.gesture = dict(point=point, px=event.x, py=event.y, moved=False,
                            dx=0 if point is None else point.x-event.xdata,
                            dz=0 if point is None else point.z-event.ydata)
        self.hide_hover()

    def motion(self, event):
        if not self.enabled:return
        self.canvas.set_cursor(Cursors.SELECT_REGION if self.inside(event) else Cursors.POINTER)
        gesture = self.gesture
        if gesture is not None and event.x is not None and event.y is not None:
            if math.hypot(event.x-gesture["px"], event.y-gesture["py"]) > 5*self.canvas.figure.dpi/100:
                gesture["moved"] = True
            point = gesture["point"]
            if point is not None:
                if gesture["moved"] and self.inside(event):
                    x, z = event.xdata+gesture["dx"], event.ydata+gesture["dz"]
                    value = self.sampler.at(x, z)
                    if value is not None:
                        point.x, point.z, point.value = x, z, value
                        point.marker.set_data([x], [z])
                        point.label.xy = (x, z)
                        point.label.set_text(f"M{point.number}: ≈ {tesla(value)}")
                        position_label(self.axes, point.label, x, z)
                self.hide_hover()
                self.canvas.draw_idle()
                return
        if self.inside(event):
            value = self.sampler.at(event.xdata, event.ydata)
            if value is not None and self.hit(event) is None:
                self.hover.xy = (event.xdata, event.ydata)
                self.hover.set_text("|B| ≈ " + tesla(value) +
                                    f"\nx={event.xdata:.4g} mm · z={event.ydata:.4g} mm".replace(".", ","))
                position_label(self.axes, self.hover, event.xdata, event.ydata)
                self.hover.set_visible(True)
            else:self.hide_hover()
        else:self.hide_hover()
        self.canvas.draw_idle()

    def release(self, event):
        gesture, self.gesture = self.gesture, None
        if gesture is None:return
        point = gesture["point"]
        close = (event.x is not None and event.y is not None and
                 math.hypot(event.x-gesture["px"], event.y-gesture["py"]) <= 5*self.canvas.figure.dpi/100)
        if not gesture["moved"] and close and self.inside(event) and event.button == MouseButton.LEFT:
            if point is not None and self.hit(event) is point:
                self.remove_artists(point)
                self.points.remove(point)
            elif point is None:
                value = self.sampler.at(event.xdata, event.ydata)
                if value is not None:
                    case = self.cases[self.case_key]
                    point = Measurement(case["next_id"], event.xdata, event.ydata, value)
                    case["next_id"] += 1
                    case["points"].append(point)
                    draw_point(self.axes, point)
        self.hide_hover()
        self.notify()
        self.canvas.draw_idle()

    def leave(self, event=None):
        self.gesture = None
        self.hide_hover()
        self.canvas.draw_idle()

    def clear(self):
        for point in self.points:self.remove_artists(point)
        self.points.clear()
        self.gesture = None
        self.hide_hover()
        self.notify()
        self.canvas.draw_idle()

    def draw_saved(self, axes, case_key):
        """Messpunkte für einen separaten PNG-Export zeichnen, ohne UI-Änderung."""
        for point in self.cases.get(case_key, {}).get("points", []):
            draw_point(axes, Measurement(point.number, point.x, point.z, point.value))
