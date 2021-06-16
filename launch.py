from pep_tk.psg.windows.gui import launch_gui
import os
import sys

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
plugin_python_lib = os.path.join(PLUGIN_PATH, 'lib', 'python3.6', 'site-packages')
sys.path.insert(0, plugin_python_lib)
sys.path.insert(0, '/data/software/viame/lib/python3.6/site-packages/')

launch_gui()