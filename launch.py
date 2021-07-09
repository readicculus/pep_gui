import os
import sys
PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
plugin_python_lib = os.path.join(PLUGIN_PATH, 'lib', 'python3.6', 'site-packages')
sys.path.insert(0, plugin_python_lib)
from pep_tk.psg.windows.create_job import launch_gui

launch_gui()