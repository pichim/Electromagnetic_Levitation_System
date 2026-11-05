"""Mausrad-Zoom und freies Verschieben der gespeicherten Magnetfeldansicht."""
from __future__ import annotations
import math
from matplotlib.backend_bases import MouseButton


class FieldNavigation:
    def __init__(self,canvas,toolbar):
        self.canvas,self.toolbar=canvas,toolbar
        self.axes,self.domain,self.home_limits,self.drag=None,None,None,None
        self.pointer_tool=None
        self.connections=[canvas.mpl_connect(name,handler) for name,handler in [
            ("scroll_event",self.scroll),("button_press_event",self.press),
            ("motion_notify_event",self.motion),("button_release_event",self.release),
            ("figure_leave_event",self.release),("key_press_event",self.key)]]

    def reset(self,axes=None,domain=None):
        """Neuer berechneter Fall erhält seine eigene Startansicht und Historie."""
        self.axes,self.domain,self.drag=axes,domain,None
        self.home_limits=None if axes is None else (axes.get_xlim(),axes.get_ylim())
        self.toolbar.update()
        if axes is not None:self.toolbar.push_current()

    def active(self,event=None):
        return (self.axes is not None and self.axes in self.canvas.figure.axes
                and (event is None or event.inaxes is None or event.inaxes is self.axes))

    def bounded(self,limits,index):
        lo,hi=limits
        span=hi-lo
        if not all(math.isfinite(v) for v in (lo,hi,span)) or span<=0:return None
        min_span=(self.home_limits[index][1]-self.home_limits[index][0])*1e-5
        if span<min_span:return None
        if self.domain is not None:
            lower,upper=self.domain[index*2:index*2+2]
            if span>=upper-lower:return (lower,upper)
            lo=max(lower,min(lo,upper-span))
            return (lo,lo+span)
        return (lo,hi)

    def set_limits(self,xlim,ylim):
        xlim,ylim=self.bounded(xlim,0),self.bounded(ylim,1)
        if xlim is None or ylim is None:return False
        if xlim==self.axes.get_xlim() and ylim==self.axes.get_ylim():return False
        self.axes.set_xlim(xlim);self.axes.set_ylim(ylim)
        self.canvas.draw_idle()
        return True

    def zoom(self,step,x=None,y=None,width_only=False):
        if not self.active() or not math.isfinite(step) or step==0:return
        ax=self.axes;xlim,ylim=ax.get_xlim(),ax.get_ylim()
        x=(xlim[0]+xlim[1])/2 if x is None else x
        y=(ylim[0]+ylim[1])/2 if y is None else y
        if not all(math.isfinite(v) for v in (x,y)):return
        factor=1.2**(-max(-8,min(8,step)))
        xs=tuple(x+(v-x)*factor for v in xlim)
        ys=ylim if width_only else tuple(y+(v-y)*factor for v in ylim)
        if self.set_limits(xs,ys):self.toolbar.push_current()

    def scroll(self,event):
        if not self.active(event) or self.drag is not None:return
        if self.pointer_tool is not None and self.pointer_tool.dragging:return
        if getattr(self.toolbar,"_pan_info",None) or getattr(self.toolbar,"_zoom_info",None):return
        # Tk übermittelt Shift auch dann zuverlässig, wenn der Plot keinen Fokus hat.
        state=getattr(getattr(event,"guiEvent",None),"state",0)
        width_only="shift" in (event.key or "").split("+") or bool(state&1)
        inside=event.inaxes is self.axes
        self.zoom(event.step,event.xdata if inside else None,event.ydata if inside else None,width_only)

    def more_width(self):
        self.zoom(-2,width_only=True)

    def less_width(self):
        self.zoom(2,width_only=True)

    def restore_view(self):
        if not self.active():return
        self.drag=None
        self.toolbar.home()

    def key(self,event):
        if self.active() and event.key in {"home","h","r"}:
            self.restore_view()

    def press(self,event):
        if not self.active(event) or event.button!=MouseButton.LEFT or self.toolbar.mode:return
        if self.pointer_tool is not None and self.pointer_tool.enabled:return
        if event.dblclick:
            self.restore_view();return
        if event.x is None or event.y is None:return
        self.drag=(event.x,event.y,self.axes.get_xlim(),self.axes.get_ylim(),
                   self.axes.transData.frozen().inverted())

    def motion(self,event):
        if self.drag is None or not self.active() or event.x is None or event.y is None:return
        x,y,xlim,ylim,inverse=self.drag
        first=inverse.transform((x,y));now=inverse.transform((event.x,event.y))
        dx,dy=now-first
        self.set_limits(tuple(v-dx for v in xlim),tuple(v-dy for v in ylim))

    def release(self,event):
        if self.drag is None:return
        _,_,xlim,ylim,_=self.drag
        self.drag=None
        if self.active() and (xlim!=self.axes.get_xlim() or ylim!=self.axes.get_ylim()):
            self.toolbar.push_current()
