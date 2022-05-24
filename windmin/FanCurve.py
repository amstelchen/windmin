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

#---------------------------------------------------------------------------

class FanCurve(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, parent)
        self.figure = Figure(figsize=(0.5, 0.5))
        self.canvas = FigureCanvas(self, -1, self.figure)
        #self.axes = self.figure.add_subplot()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.draw()
        self.Fit()

    def draw(self, current_temp=0):
        #t = arrange(0.0, 3.0, 0.01)
        #s = sin(2 * pi * t)
        #print("in draw()")

        temp = (20, 40, 50, 70, 90, 100)
        rpm = (0, 0, 20, 50, 85, 100)
        self.Refresh(eraseBackground=True)
        self.axes = self.figure.add_subplot()
        self.axes.plot(temp, [str(rpm)+"%" for rpm in rpm])
        self.axes.plot(current_temp, 1, 'bo')
        #print(current_temp)
        #self.axes.update_params()
        self.canvas.draw()
