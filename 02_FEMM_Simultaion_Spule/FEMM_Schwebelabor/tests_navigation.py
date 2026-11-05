"""Navigation prüfen, ohne einen FEMM-Lauf oder ein Tk-Fenster zu starten."""
import unittest
from types import SimpleNamespace
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import NavigationToolbar2,MouseEvent,KeyEvent
from plot_navigation import FieldNavigation


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.figure=Figure(figsize=(8,6));self.canvas=FigureCanvasAgg(self.figure)
        self.ax=self.figure.add_subplot(111);self.ax.set_aspect('equal',adjustable='box')
        self.ax.set_xlim(-50,50);self.ax.set_ylim(-100,100)
        self.canvas.draw()
        self.toolbar=NavigationToolbar2(self.canvas)
        self.nav=FieldNavigation(self.canvas,self.toolbar)
        self.nav.reset(self.ax,(-500,500,-500,500))

    def event(self,name,x=15,y=30,**kwargs):
        px,py=self.ax.transData.transform((x,y))
        return MouseEvent(name,self.canvas,px,py,**kwargs)

    def test_scroll_is_cursor_anchored_and_reversible(self):
        e=self.event('scroll_event',step=1)
        oldx,oldy=self.ax.get_xlim(),self.ax.get_ylim()
        relative=((e.xdata-oldx[0])/(oldx[1]-oldx[0]),(e.ydata-oldy[0])/(oldy[1]-oldy[0]))
        self.canvas.callbacks.process('scroll_event',e)
        xs,ys=self.ax.get_xlim(),self.ax.get_ylim()
        self.assertLess(xs[1]-xs[0],100);self.assertLess(ys[1]-ys[0],200)
        np.testing.assert_allclose(((e.xdata-xs[0])/(xs[1]-xs[0]),(e.ydata-ys[0])/(ys[1]-ys[0])),relative)
        self.nav.zoom(-1,e.xdata,e.ydata)
        np.testing.assert_allclose(self.ax.get_xlim(),oldx);np.testing.assert_allclose(self.ax.get_ylim(),oldy)

    def test_shift_and_button_reveal_more_width_without_changing_height(self):
        oldy=self.ax.get_ylim();oldbox=self.ax.get_window_extent().width
        e=self.event('scroll_event',step=-1,guiEvent=SimpleNamespace(state=1))
        self.canvas.callbacks.process('scroll_event',e)
        self.assertGreater(np.diff(self.ax.get_xlim())[0],100)
        self.assertEqual(self.ax.get_ylim(),oldy)
        self.assertGreater(self.ax.get_window_extent().width,oldbox)
        self.nav.more_width();self.assertEqual(self.ax.get_ylim(),oldy)

    def test_drag_preserves_scale_and_toolbar_mode_owns_mouse(self):
        before=(self.ax.get_xlim(),self.ax.get_ylim())
        start=self.event('button_press_event',button=1);self.nav.press(start)
        e=MouseEvent('motion_notify_event',self.canvas,start.x+40,start.y+20,button=1)
        self.nav.motion(e);self.nav.release(e)
        after=(self.ax.get_xlim(),self.ax.get_ylim())
        self.assertNotEqual(after,before)
        np.testing.assert_allclose([np.diff(v)[0] for v in after],[100,200])
        self.toolbar.home()
        self.toolbar.pan();self.nav.press(start);self.assertIsNone(self.nav.drag)

    def test_home_back_and_new_case_history(self):
        original=(self.ax.get_xlim(),self.ax.get_ylim())
        self.nav.zoom(1);first=(self.ax.get_xlim(),self.ax.get_ylim())
        self.nav.zoom(1);self.toolbar.back()
        np.testing.assert_allclose((self.ax.get_xlim(),self.ax.get_ylim()),first)
        self.toolbar.home()
        np.testing.assert_allclose((self.ax.get_xlim(),self.ax.get_ylim()),original)
        self.figure.clear();other=self.figure.add_subplot(111)
        other.set_xlim(-3,7);other.set_ylim(-10,20)
        self.nav.reset(other,(-50,50,-50,50));self.nav.zoom(1);self.toolbar.home()
        np.testing.assert_allclose((other.get_xlim(),other.get_ylim()),((-3,7),(-10,20)))

    def test_empty_canvas_colourbar_and_domain_bounds(self):
        self.nav.reset();e=self.event('scroll_event',step=1)
        self.canvas.callbacks.process('scroll_event',e)
        self.assertEqual(self.ax.get_xlim(),(-50,50))
        self.nav.reset(self.ax,(-500,500,-500,500))
        other=self.figure.add_axes([.9,.1,.03,.6]);before=self.ax.get_xlim()
        e.inaxes=other;self.nav.scroll(e);self.assertEqual(before,self.ax.get_xlim())
        for _ in range(30):self.nav.zoom(-8)
        self.assertEqual(self.ax.get_xlim(),(-500,500));self.assertEqual(self.ax.get_ylim(),(-500,500))
        for _ in range(70):self.nav.zoom(8)
        self.assertGreater(np.diff(self.ax.get_xlim())[0],.0009)
        self.assertGreater(np.diff(self.ax.get_ylim())[0],.0019)

    def test_blank_canvas_scroll_and_double_click_home(self):
        e=MouseEvent('scroll_event',self.canvas,3,3,step=1)
        self.assertIsNone(e.inaxes);self.nav.scroll(e)
        self.assertLess(np.diff(self.ax.get_xlim())[0],100)
        e=self.event('button_press_event',button=1,dblclick=True)
        self.nav.press(e)
        np.testing.assert_allclose((self.ax.get_xlim(),self.ax.get_ylim()),((-50,50),(-100,100)))
        self.nav.zoom(1)
        self.canvas.callbacks.process('key_press_event',KeyEvent('key_press_event',self.canvas,'home'))
        np.testing.assert_allclose((self.ax.get_xlim(),self.ax.get_ylim()),((-50,50),(-100,100)))


if __name__=='__main__':unittest.main(verbosity=2)
