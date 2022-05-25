import sys
import wx
import subprocess

VERSION = "0.1.0"
__appname__ = "Windmin"
__version__ = VERSION
__author__ = "Michael John"
__copyright__ = \
'Copyright © 2022 Michael John <michael.john@gmx.at>'
__licence__ = \
'Lizenz GPLv3: GNU GPL Version 3 oder neuer\n<https://gnu.org/licenses/gpl.html>\n' \
'Dies ist freie Software; es steht Ihnen frei, sie zu verändern und weiterzugeben. ' \
'Es gibt KEINE GARANTIE, soweit als vom Gesetz erlaubt.\n' \
'Geschrieben von Michael John.'

def PrintAbout() -> str:
    sensorsVersion = subprocess.run(["sensors", "-v"], capture_output=True, text=True).stdout.replace('version', 'Version: ').replace('with ','\n')
    returnString = (f'\n{__appname__} Version: {__version__}\n'
        f'Python Version: {".".join([str(value) for value in sys.version_info[0:3]])}\n'
        #f'ttkbootstrap Version: {version("ttkbootstrap"):s}\n'
        f'wxWidgets Version: {"3.0.5":s}\n'
        f'wxPython Version: {wx.__version__:s}\n'
        f'{sensorsVersion}\n'
        f'\n{__copyright__}\n'
        f'\n{__licence__}\n')
    return returnString
