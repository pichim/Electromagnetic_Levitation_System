"""Upright 3D orbit, wheel zoom and view presets for the force-map canvas."""
from __future__ import annotations
import math
import numpy as np
from matplotlib.backend_bases import MouseButton


PRESETS = {
    "Perspektive": (28, -135),
    "Kraft / Strom": (0, -90),
    "Kraft / Luftspalt": (0, 0),
    "Draufsicht": (90, -90),
}


class ForceMapNavigation:
    def __init__(self, canvas, toolbar):
        self.canvas, self.toolbar = canvas, toolbar
        self.axes = self.home_limits = self.drag = None
        self.zoom_level = 1.08
        self.connections = [canvas.mpl_connect(name, callback) for name, callback in (
            ("scroll_event", self.scroll), ("button_press_event", self.press),
            ("motion_notify_event", self.motion), ("button_release_event", self.release),
            ("figure_leave_event", self.release), ("key_press_event", self.key))]

    def active(self, event=None):
        return (self.axes is not None and self.axes in self.canvas.figure.axes
                and (event is None or event.inaxes is None or event.inaxes is self.axes))

    def snapshot(self):
        if not self.active(): return None
        limits = (self.axes.get_xlim(), self.axes.get_ylim(), self.axes.get_zlim())
        offsets = [(sum(now)-sum(home))/(2*(home[1]-home[0]))
                   for now, home in zip(limits, self.home_limits)]
        return dict(elev=self.axes.elev, azim=self.axes.azim,
                    zoom=self.zoom_level, offsets=offsets)

    def reset(self, axes=None, state=None):
        self.axes, self.drag = axes, None
        self.home_limits = None
        self.zoom_level = 1.08
        if axes is not None:
            # Handle orbit ourselves: identical behaviour on Matplotlib 3.8 and later.
            axes.disable_mouse_rotation()
            self.home_limits = (axes.get_xlim(), axes.get_ylim(), axes.get_zlim())
        self.toolbar.update()
        if axes is not None:
            self.toolbar.push_current()
            if state:
                axes.view_init(elev=state["elev"], azim=state["azim"], roll=0)
                self.zoom_level = state["zoom"]
                axes.set_box_aspect((1.2, 1.05, .85), zoom=self.zoom_level)
                self.set_limits([tuple(v+offset*(home[1]-home[0]) for v in home)
                                 for home, offset in zip(self.home_limits, state["offsets"])])
                self.toolbar.push_current()

    def normal_mode(self):
        # Explicit buttons also work if a toolbar tool was left active.
        if self.toolbar.mode == "pan/zoom": self.toolbar.pan()
        elif self.toolbar.mode == "zoom rect": self.toolbar.zoom()

    def set_limits(self, limits):
        self.axes.set_xlim(limits[0]); self.axes.set_ylim(limits[1]); self.axes.set_zlim(limits[2])

    def zoom(self, step):
        if not self.active() or not math.isfinite(step) or step == 0: return
        self.normal_mode()
        level = max(.55, min(2.2, self.zoom_level*1.12**max(-8, min(8, step))))
        if level == self.zoom_level: return
        self.zoom_level = level
        # Camera magnification changes; the force axes and data remain meaningful.
        self.axes.set_box_aspect((1.2, 1.05, .85), zoom=level)
        self.canvas.draw_idle()

    def scroll(self, event):
        if self.active(event) and self.drag is None and not self.toolbar.mode:
            self.zoom(event.step)

    def restore_view(self):
        if not self.active(): return
        self.normal_mode()
        self.drag = None
        self.set_limits(self.home_limits)
        self.zoom_level = 1.08
        self.axes.set_box_aspect((1.2, 1.05, .85), zoom=self.zoom_level)
        self.axes.view_init(elev=28, azim=-135, roll=0)
        self.toolbar.push_current()
        self.canvas.draw_idle()

    def preset(self, name):
        if not self.active(): return
        self.normal_mode()
        elev, azim = PRESETS[name]
        self.axes.view_init(elev=elev, azim=azim, roll=0)
        self.toolbar.push_current()
        self.canvas.draw_idle()

    def press(self, event):
        if not self.active(event) or self.toolbar.mode: return
        if event.button == MouseButton.LEFT and event.dblclick:
            self.restore_view(); return
        if event.button not in (MouseButton.LEFT, MouseButton.MIDDLE, MouseButton.RIGHT): return
        if event.x is None or event.y is None: return
        shift = "shift" in (event.key or "").split("+")
        shift = shift or bool(getattr(getattr(event, "guiEvent", None), "state", 0) & 1)
        self.drag = dict(x=event.x, y=event.y, elev=self.axes.elev, azim=self.axes.azim,
                         pan=shift or event.button != MouseButton.LEFT,
                         limits=(self.axes.get_xlim(), self.axes.get_ylim(), self.axes.get_zlim()))

    def motion(self, event):
        if self.drag is None or not self.active() or event.x is None or event.y is None: return
        d = self.drag
        width, height = max(1, self.axes.bbox.width), max(1, self.axes.bbox.height)
        dx, dy = (event.x-d["x"])/width, (event.y-d["y"])/height
        if d["pan"]:
            azim, elev = math.radians(d["azim"]), math.radians(d["elev"])
            right = np.array([-math.sin(azim), math.cos(azim), 0])
            up = np.array([-math.sin(elev)*math.cos(azim),
                           -math.sin(elev)*math.sin(azim), math.cos(elev)])
            spans = np.array([hi-lo for lo, hi in d["limits"]])
            aspect = np.array([1.2, 1.05, .85])
            delta = -(dx*right+dy*up)*spans/aspect/self.zoom_level*1.8
            self.set_limits([tuple(v+shift for v in limits) for limits, shift in zip(d["limits"], delta)])
        else:
            self.axes.view_init(elev=max(-89, min(89, d["elev"]-dy*180)),
                                azim=(d["azim"]-dx*240+180)%360-180, roll=0)
        self.canvas.draw_idle()

    def release(self, event):
        if self.drag is None: return
        self.drag = None
        if self.active(): self.toolbar.push_current()

    def key(self, event):
        if not self.active(): return
        if event.key in {"home", "h", "r"}: self.restore_view()
        elif event.key in {"+", "="}: self.zoom(1)
        elif event.key in {"-", "_"}: self.zoom(-1)
