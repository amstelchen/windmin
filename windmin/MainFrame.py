# -*- coding: UTF-8 -*-
#
# generated by wxGlade 1.1.0pre on Thu May 19 20:31:29 2022
#

import wx
import os
import sys
import re
import glob
import gettext
import webbrowser
import subprocess
import psutil
import time
from importlib_metadata import version
# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
from .FanCurve import FanCurve
from .Version import PrintAbout, __appname__, __version__, __author__, __copyright__, __licence__
# end wxGlade

gettext = gettext.translation('windmin', localedir=os.path.join(os.path.dirname(__file__), 'locales'))
gettext.install("windmin")
_ = gettext.gettext

hwmon_files = []
pwm_files = []
temp_files = []

DEBUG=True

def debug_print(message, prefix="DEBUG: ", end="\n"):
    global DEBUG
    try:
        if os.environ['DEBUG'] == "1" and DEBUG:
            print(f"{prefix}{message}", end=end, flush=True)
    except KeyError:
        pass

WinPos = (-1, -1)
Profiles = []

def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False;

def config_load():
    global Profiles
    global WinPos
    WinPos = wx.Point(-1, -1)

    config_path = os.path.expanduser("~/.config/windmin")
    config_file = os.path.join(config_path,"windmin.conf")

    if not os.path.exists(config_path):
        os.mkdir(os.path.join(os.path.expanduser("~/.config"),"windmin"))

    if os.path.exists(config_file):
        #print(config_file)
        config_desc = open(os.path.join(config_path, "windmin.conf"), 'r', newline="\n")
        lines = config_desc.readlines()
        for line in lines:
            if "Profile" in line:
                ProfileNum, ProfileName, ProfileContents = re.split('\b\d|=|,',line.strip(), maxsplit=2)
                Profiles.append((ProfileName, ProfileContents))
        WinPos = wx.Point(int(lines[1].split('=')[1].rstrip()), int(lines[2].split('=')[1].rstrip()))
        debug_print(_("Configuration loaded."))
        #print(Profiles)
    else:
        config_desc = open(config_file, 'w', newline="\n")
        lines = ["Category=Length\n", "WinPosX=200\n", "WinPosY=200\n"]
        config_desc.writelines(lines)
        debug_print(_("Configuration not found, recreating."))

def config_save(WinPos):
    global Profiles
    
    config_path = os.path.expanduser("~/.config/windmin/windmin.conf")
    if not os.path.exists(config_path):
        os.mkdir(os.path.join(os.path.expanduser("~/.config"),"windmin"))
    config_file = open(config_path, 'w', newline="\n")
    lines = ["Category=Length\n", "WinPosX=" + str(WinPos.x) + "\n", "WinPosY=" + str(WinPos.y) + "\n"]
    config_file.writelines(lines)
    for index, profile in enumerate(Profiles):
        config_file.writelines("Profile" + str(index) + "=" + ','.join(profile) + "\n")
    debug_print(_("Configuration saved."))

def config_apply(ProfileNum):
    global Profiles
    
    config_file = os.path.expanduser("/etc/fancontrol")
    if not os.path.exists(config_file):
        debug_print(config_file + " not found.")
        return
    try:
        config_file = open(config_file, 'w', newline="\n")
        comment_line= "# This file was created by Windmin" + "\n"
        config_file.writelines(comment_line)
        config_file.writelines(Profiles[ProfileNum] + "\n")
        debug_print(_("Configuration applied."))
    except PermissionError:
        pass
    if checkIfProcessRunning("fancontrol"):
        debug_print(_("Restarting fancontrol service daemon... "), end="")
    else:
        debug_print(_("fancontrol service daemon not up, starting... "), end="")
    try:
        subprocess.run(["pkexec", "systemctl", "restart", "fancontrol.service"])
    except PermissionError:
        pass
    if checkIfProcessRunning("fancontrol"):
        debug_print(_("done."),prefix="")

def ask(parent=None, message='', default_value=''):
    dlg = wx.TextEntryDialog(parent, message, value=default_value)
    dlg.SetTitle("Windmin")
    dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    return result

def read_hwmon():
    global hwmon_files, pwm_files, temp_files

    hwmon_files = []
    for hwmon_file in sorted(glob.glob("/sys/class/hwmon/hwmon?")):
        debug_print(hwmon_file, end=": ")
        with open(hwmon_file + "/name") as f:
            contents = f.read()
            hwmon_files.append(os.path.basename(hwmon_file) + "/" + contents + "::")
            debug_print(contents, prefix="", end=": ")
            for hwmon_subfile in sorted(glob.glob("/sys/class/hwmon/" + os.path.basename(hwmon_file) + "/*_input")):
                with open(hwmon_subfile) as f:
                    try:
                        contents_sub = f.read()
                        if "freq" in hwmon_subfile:
                            contents_sub = str(int(int(contents_sub) // 1e6)).rjust(4) + " MHz"
                        if "temp" in hwmon_subfile:
                            contents_sub = str(int(contents_sub) // 1000).rjust(4) + " °C"
                        if "fan" in hwmon_subfile and int(contents_sub.strip()) == 0 and contents.strip() == "amdgpu":
                            contents_sub = contents_sub.rjust(5) + "RPM (not reported)"
                        elif "fan" in hwmon_subfile:
                            contents_sub = contents_sub.rjust(5) + "RPM"
                        if os.path.basename(hwmon_subfile).startswith("in"):
                            contents_sub = contents_sub.rjust(5) + "mV"
                    except OSError:
                        # https://github.com/nicolargo/glances/issues/1203
                        contents_sub = " N/A °C (WiFi disabled)"
                    hwmon_files.append(os.path.basename(hwmon_subfile) + ": " + contents_sub)
                    debug_print(hwmon_subfile + ": " + contents, end="")
        hwmon_files.append("::")
    hwmon_files.pop()

    pwm_files = []
    for pwm_file in sorted(glob.glob("/sys/class/hwmon/hwmon*/" + 'pwm?')):
        pwm_files.append(os.path.basename(pwm_file).replace('pwm', 'Fan '))
        with open(pwm_file) as f:
            contents = f.read()
            debug_print(pwm_file + ": " + contents, end="")

    temp_files = []
    for temp_file in glob.glob("/sys/class/hwmon/hwmon*/" + 'temp?_label'):
        debug_print(temp_file, end=": ")
        with open(temp_file) as f:
            label = f.read().strip()
            debug_print(label.ljust(22), prefix="", end=": ")
        with open(temp_file.replace('label', 'input')) as f:
            value = f.read().strip()
            if int(value) > 0:
                temp_files.append(f"{label}: {int(value) / 1000}°C")
            debug_print(value, prefix="")


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        global hwmon_files, pwm_files, temp_files

        # begin wxGlade: MainFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.SYSTEM_MENU
        
        config_load()
        read_hwmon()

        wx.Frame.__init__(self, *args, **kwds)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefresh)
        self.timer.Start(1000)  #10 minutes

        self.SetSize(wx.DLG_UNIT(self, wx.Size(250, 300)))
        self.SetMinSize(wx.DLG_UNIT(self, wx.Size(250, 300)))
        debug_print(f"WinPos: {WinPos}")
        self.SetPosition(wx.Point(WinPos))
        self.SetTitle(__appname__)
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(wx.Bitmap(os.path.join(os.path.dirname(__file__), 'images/windmin.png'), wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)

        # Menu Bar
        self.frame1_menubar = wx.MenuBar()
        self.menuFile = wx.Menu()
        self.frame1_menubar.itemQuit = self.menuFile.Append(wx.ID_ANY, _("Quit"), "")
        self.Bind(wx.EVT_MENU, self.btnQuit_click, self.frame1_menubar.itemQuit)
        self.frame1_menubar.Append(self.menuFile, _("File"))
        self.itemHelp = wx.Menu()
        self.frame1_menubar.subitemHelp = self.itemHelp.Append(wx.ID_ANY, _("Help"), "")
        self.Bind(wx.EVT_MENU, self.btnHelp_click, self.frame1_menubar.subitemHelp)
        self.frame1_menubar.subitemAbout = self.itemHelp.Append(wx.ID_ANY, _("About"), "")
        self.Bind(wx.EVT_MENU, self.btnAbout_click, self.frame1_menubar.subitemAbout)
        self.frame1_menubar.Append(self.itemHelp, _("Help"))
        self.SetMenuBar(self.frame1_menubar)
        # Menu Bar end

        # Tool Bar
        self.frame1_toolbar = wx.ToolBar(self, -1)
        tool = self.frame1_toolbar.AddTool(wx.ID_ANY, _("Apply"), wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR, (24, 24)), wx.NullBitmap, wx.ITEM_NORMAL, "", "")
        self.Bind(wx.EVT_TOOL, self.btnApply_click, id=tool.GetId())
        tool = self.frame1_toolbar.AddTool(wx.ID_ANY, _("Reset"), wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, (24, 24)), wx.NullBitmap, wx.ITEM_NORMAL, "", "")
        self.Bind(wx.EVT_TOOL, self.btnReset_click, id=tool.GetId())
        self.frame1_toolbar.AddSeparator()
        tool = self.frame1_toolbar.AddTool(wx.ID_ANY, _("Profile"), wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_TOOLBAR, (24, 24)), wx.NullBitmap, wx.ITEM_NORMAL, "", "")
        self.Bind(wx.EVT_TOOL, self.btnProfile_click, id=tool.GetId())
        tool = self.frame1_toolbar.AddTool(wx.ID_ANY, _("Harddisk"), wx.ArtProvider.GetBitmap(wx.ART_HARDDISK, wx.ART_TOOLBAR, (24, 24)), wx.NullBitmap, wx.ITEM_NORMAL, "", "")
        self.Bind(wx.EVT_TOOL, self.btnHarddisk_click, id=tool.GetId())
        self.frame1_toolbar.AddSeparator()
        tool = self.frame1_toolbar.AddTool(wx.ID_ANY, _("About"), wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR, (24, 24)), wx.NullBitmap, wx.ITEM_NORMAL, "", "")
        self.Bind(wx.EVT_TOOL, self.btnAbout_click, id=tool.GetId())
        tool = self.frame1_toolbar.AddTool(wx.ID_ANY, _("Quit"), wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR, (24, 24)), wx.NullBitmap, wx.ITEM_NORMAL, "", "")
        self.Bind(wx.EVT_TOOL, self.btnQuit_click, id=tool.GetId())
        self.SetToolBar(self.frame1_toolbar)
        self.frame1_toolbar.Realize()
        # Tool Bar end

        self.notebook_1 = wx.Notebook(self, wx.ID_ANY)

        self.Sensors = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.Sensors, _("Sensors"))

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.list_ctrl_1 = wx.ListCtrl(self.Sensors, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_NO_HEADER) # | wx.LC_HRULES | wx.LC_VRULES)
        self.list_ctrl_1.AppendColumn(_("Sensor"), format=wx.LIST_FORMAT_LEFT, width=275)
        self.list_ctrl_1.AppendColumn(_("Value"), format=wx.LIST_FORMAT_LEFT, width=200)
        #self.list_ctrl_1.SetFont(wx.Font("Monospace"))
        #self.list_ctrl_1.ScrollList(0, -1000)
        #self.list_ctrl_1.SetEvtHandlerEnabled(False)
        sizer_1.Add(self.list_ctrl_1, 1, wx.EXPAND, 0)

        self.Fans = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.Fans, _("Fans"))

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        sizer_11 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(sizer_11, 1, wx.EXPAND, 0)

        self.ListBoxFans = wx.ListBox(self.Fans, wx.ID_ANY, choices=pwm_files)
        self.ListBoxFans.SetMinSize((60, 350))
        sizer_11.Add(self.ListBoxFans, 0, wx.EXPAND, 0)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        sizer_11.Add(sizer_5, 0, 0, 0)

        self.panelCurve = FanCurve(self.Fans)
        sizer_5.Add(self.panelCurve, 2, wx.EXPAND, 0)

        sizer_5.Add((20, 20), 0, 0, 0)

        grid_sizer_1 = wx.GridBagSizer(10, 10)
        sizer_5.Add(grid_sizer_1, 1, wx.ALL | wx.EXPAND, 10)

        self.checkbox_2 = wx.CheckBox(self.Fans, wx.ID_ANY, "")
        grid_sizer_1.Add(self.checkbox_2, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)

        label_4 = wx.StaticText(self.Fans, wx.ID_ANY, _("Controlled by:"))
        label_4.SetMinSize(wx.DLG_UNIT(label_4, wx.Size(70, 8)))
        grid_sizer_1.Add(label_4, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_1 = wx.ComboBox(self.Fans, wx.ID_ANY, choices=temp_files, style=wx.CB_DROPDOWN)
        self.combo_box_1.SetMinSize(wx.DLG_UNIT(self.combo_box_1, wx.Size(100, 14)))
        grid_sizer_1.Add(self.combo_box_1, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL, 0)

        label_1 = wx.StaticText(self.Fans, wx.ID_ANY, _("Delay in number of cycles:"), style=wx.ALIGN_CENTER_HORIZONTAL)
        grid_sizer_1.Add(label_1, (1, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)

        self.slider_2 = wx.Slider(self.Fans, wx.ID_ANY, 0, 0, 10)
        grid_sizer_1.Add(self.slider_2, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)

        self.checkbox_3 = wx.CheckBox(self.Fans, wx.ID_ANY, "")
        grid_sizer_1.Add(self.checkbox_3, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL, 0)

        label_3 = wx.StaticText(self.Fans, wx.ID_ANY, _("Turn fan off if temp < MINTEMP"))
        grid_sizer_1.Add(label_3, (2, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)

        label_2 = wx.StaticText(self.Fans, wx.ID_ANY, _("pwm value for fan to start:"))
        grid_sizer_1.Add(label_2, (3, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)

        self.slider_1 = wx.Slider(self.Fans, wx.ID_ANY, 0, 0, 10)
        grid_sizer_1.Add(self.slider_1, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)

        self.Profiles = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.Profiles, _("Profiles"))

        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(sizer_6, 1, wx.ALL | wx.EXPAND, 30)

        self.listboxProfiles = wx.ListBox(self.Profiles, wx.ID_ANY, choices=[_("Default Profile")])
        self.listboxProfiles.SetMinSize(wx.DLG_UNIT(self.listboxProfiles, wx.Size(100, 100)))
        sizer_6.Add(self.listboxProfiles, 0, wx.RIGHT, 10)

        sizer_10 = wx.BoxSizer(wx.VERTICAL)
        sizer_6.Add(sizer_10, 1, wx.EXPAND, 0)

        self.btnApply = wx.Button(self.Profiles, wx.ID_ANY, _("Apply Profile"))
        sizer_10.Add(self.btnApply, 0, 0, 0)

        self.btnCreate = wx.Button(self.Profiles, wx.ID_ANY, _("Create new Profile"))
        sizer_10.Add(self.btnCreate, 0, 0, 0)

        self.btnSave = wx.Button(self.Profiles, wx.ID_ANY, _("Save Profile"))
        sizer_10.Add(self.btnSave, 0, 0, 0)

        self.btnDelete = wx.Button(self.Profiles, wx.ID_ANY, _("Delete Profile"))
        sizer_10.Add(self.btnDelete, 0, 0, 0)

        self.Settings = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.Settings, _("Settings"))

        sizer_4 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_3 = wx.GridBagSizer(0, 0)
        sizer_4.Add(grid_sizer_3, 1, wx.ALL | wx.EXPAND, 30)

        self.About = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.About, _("About"))

        sizer_7 = wx.BoxSizer(wx.VERTICAL)

        sizer_8 = wx.BoxSizer(wx.VERTICAL)
        sizer_7.Add(sizer_8, 1, wx.ALL | wx.EXPAND, 30)

        self.bitmap_button_1 = wx.BitmapButton(self.About, wx.ID_ANY, wx.Bitmap(os.path.join(os.path.dirname(__file__), 'images/windmin.png'), wx.BITMAP_TYPE_ANY))
        self.bitmap_button_1.SetSize(self.bitmap_button_1.GetBestSize())
        sizer_8.Add(self.bitmap_button_1, 0, 0, 15)

        sizer_9 = wx.BoxSizer(wx.VERTICAL)
        sizer_8.Add(sizer_9, 1, wx.EXPAND | wx.LEFT, 5)

        label_5 = wx.StaticText(self.About, wx.ID_ANY, __appname__)
        label_5.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_9.Add(label_5, 0, wx.TOP, 10)

        label_6 = wx.StaticText(self.About, wx.ID_ANY, _("Yet another GUI for fancontrol"), style=wx.ST_NO_AUTORESIZE)
        sizer_9.Add(label_6, 0, 0, 0)

        label_7 = wx.StaticText(self.About, wx.ID_ANY, PrintAbout())
        sizer_9.Add(label_7, 0, 0, 0)

        self.About.SetSizer(sizer_7)

        self.Settings.SetSizer(sizer_4)

        self.Profiles.SetSizer(sizer_3)

        self.Fans.SetSizer(sizer_2)

        self.Sensors.SetSizer(sizer_1)

        self.Layout()
        #self.Centre()

        self.panelCurve.draw(-1, -1)

        self.btnApply.Bind(wx.EVT_BUTTON, self.btnApplyProfile_click)
        self.btnCreate.Bind(wx.EVT_BUTTON, self.btnCreateProfile_click)
        self.btnSave.Bind(wx.EVT_BUTTON, self.btnSaveProfile_click)
        self.btnDelete.Bind(wx.EVT_BUTTON, self.btnDeleteProfile_click)

        #self.list_ctrl_1.SetAlternateRowColour(wx.Colour(wx.BLUE))
        #self.list_ctrl_1.EnableAlternateRowColours(True)

        #self.listboxProfiles.Clear()
        for index, profile in enumerate(Profiles):
            self.listboxProfiles.Insert(profile[0], index)

        # end wxGlade

    def btnApply_click(self, event):  # wxGlade: MainFrame.<event_handler>
        self.panelCurve.draw(current_rpm=self.ListBoxFans.GetSelection())
        self.Refresh()
        #print(pwm_files.index(3).value)
        event.Skip()

    def btnReset_click(self, event):  # wxGlade: MainFrame.<event_handler>
        self.OnRefresh(wx.EVT_TIMER)

        event.Skip()

    def btnProfile_click(self, event):  # wxGlade: MainFrame.<event_handler>
        self.notebook_1.SetSelection(2)
        event.Skip()

    def btnHelp_click(self, event):  # wxGlade: MainFrame.<event_handler>
        url = 'https://github.com/amstelchen/windmin'
        webbrowser.open(url)
        event.Skip()

    def btnAbout_click(self, event):  # wxGlade: MainFrame.<event_handler>
        self.notebook_1.SetSelection(4)
        event.Skip()

    def btnQuit_click(self, event):  # wxGlade: MainFrame.<event_handler>
        config_save(self.GetPosition())
        quit()
        event.Skip()

    def btnFile_click(self, event):  # wxGlade: MainFrame.<event_handler>
        event.Skip()

    def btnApplyProfile_click(self, event):  # wxGlade: MainFrame.<event_handler>
        config_apply(self.listboxProfiles.GetSelection() - 1)
        event.Skip()

    def btnCreateProfile_click(self, event):  # wxGlade: MainFrame.<event_handler>
        global Profiles
        ProfileName = ask(message = 'Please name your profile')
        if len(ProfileName) > 0: # and ProfileName.isalnum():
            self.listboxProfiles.Insert(ProfileName, self.listboxProfiles.Count)
            Profiles.append((ProfileName, "ProfileProp"))
        event.Skip()

    def btnDeleteProfile_click(self, event):  # wxGlade: MainFrame.<event_handler>
        self.listboxProfiles.Delete(self.listboxProfiles.GetSelection())
        event.Skip()

    def btnSaveProfile_click(self, event):  # wxGlade: MainFrame.<event_handler>
        config_save(self.GetPosition())
        event.Skip()

    def btnHarddisk_click(self, event):  # wxGlade: MainFrame.<event_handler>
        try:
            subprocess.run(["pkexec", "modprobe", "drivetemp"])
            subprocess.call(["windmin"])
            quit()
        except PermissionError:
            pass
        event.Skip()

    def OnRefresh(self,event):
        global hwmon_files, pwm_files, temp_files
        global Profiles

        if self.list_ctrl_1.ItemCount > 0:
            self.list_ctrl_1.DeleteAllItems()
        
        for index, entry in enumerate(hwmon_files):
            if "::" in entry:
                item = self.list_ctrl_1.InsertItem(index, entry.split(':')[0])
                self.list_ctrl_1.SetItemFont(item, wx.Font("Monospace 12 bold"))
            else:
                item = self.list_ctrl_1.InsertItem(index, entry.split(':')[0])
                self.list_ctrl_1.SetItem(item, 1, entry.split(':')[1])
                self.list_ctrl_1.SetItemFont(item, wx.Font("Monospace 10"))

        read_hwmon()
        selectedItem = self.combo_box_1.GetCurrentSelection()
        self.combo_box_1.Clear()
        self.combo_box_1.AppendItems(temp_files)
        self.combo_box_1.SetSelection(selectedItem)

        self.Refresh()
        for i, s in enumerate(temp_files):
            if self.combo_box_1.Value.split(':')[0] in s:
              current_temp = temp_files[i].split(':')[1].split('.')[0]

        #print(pwm_files)
        selectedFan = self.ListBoxFans.GetSelection()
        debug_print(selectedFan)

        for pwm_file in sorted(glob.glob("/sys/class/hwmon/hwmon*/" + 'pwm' + str(selectedFan))):
            debug_print(pwm_file)
            with open(pwm_file) as f:
                contents = f.read()
                debug_print(pwm_file + ": " + contents, end="")
                if True:
                    current_rpm = round((float(contents) / 255.0) * 100.0, 0)
                    self.panelCurve.draw(current_temp, current_rpm)
                    debug_print(f"{current_temp}, {current_rpm}")

        #print(temp_files)

# end of class MainFrame
