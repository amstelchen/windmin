import os
import sys
import wx
#from wx.lib import plot as wxplot

from numpy import arange, sin, pi
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

import random

#---------------------------------------------------------------------------

class FanCurve(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        
        wx.Panel.__init__(self, parent)

        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.OnRefresh)
        #self.timer.Start(1000)  #10 minutes

        self.figure = Figure(figsize=(0.5, 0.5))
        self.canvas = FigureCanvas(self, -1, self.figure)
        #self.axes = self.figure.add_subplot()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.ALL | wx.GROW, 0)
        self.SetSizer(self.sizer)
        #self.draw()
        self.Fit()
        #self.Bind(wx.MOUSE_BTN_ANY, self.handle_update)

    def OnRefresh(self,event):
        #self.Refresh(eraseBackground=True)
        #self.canvas.ClearBackground()
        self.figure.clear()
        self.draw()

    def draw(self, current_temp=60, current_rpm=70):
        #t = arrange(0.0, 3.0, 0.01)
        #s = sin(2 * pi * t)
        #print("in draw()")

        #temp = (20, 40, 50, 70, 90, 100)
        temp = range(20, 100, 10)  # = 8
        rpm = (0, 0, 30, 50, 50, 70, 85, 100)

        #current_temp = round(random.randint(30, 80), -1)
        #current_rpm = self.parent.ListBoxFans[0].value
        
        current_temp = min(temp, key=lambda x:abs(x-int(current_temp)))
        current_rpm = min(rpm, key=lambda x:abs(x-current_rpm))
        #debug_print(f"{current_temp}, {current_rpm}")

        self.figure.clear()
        self.Refresh(eraseBackground=True)
        self.axes = self.figure.add_subplot()
        #self.axes.autoscale_view(tight=None,scalex=True,scaley=True)
        self.axes.plot([str(temp)+"°C" for temp in temp], [str(rpm)+"%" for rpm in rpm])
        self.axes.plot(str(current_temp)+"°C", str(current_rpm)+"%", 'bo')
        #print(current_temp)
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        #self.axes.update_params()
        #self.canvas.draw()

    def handle_update(self, event):
        #self.draw()
        self.axes.update_params()
