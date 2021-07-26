import os
import sys


PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
plugin_python_lib = os.path.join(PLUGIN_PATH, 'lib', 'python3.6', 'site-packages')
sys.path.insert(0, plugin_python_lib)
from pep_tk.psg.windows.create_job import launch_gui
from pep_tk.core.parser import DatasetManifestError

def main():
    try:
        launch_gui()
    except DatasetManifestError as e:
        import PySimpleGUI as sg
        from pep_tk.psg.windows import initial_setup

        if hasattr(e, 'message'):
            msg = f'Error Type:\n{e.__class__.__name__}\nMessage:\n{e.message}'
        else:
            msg = str(e)

        sg.popup_ok(msg, title="uh oh")
        initial_setup(skip_if_complete=False)
        main()
    except Exception as e:
        import PySimpleGUI as sg

        if hasattr(e, 'message'):
            msg = f'Error Type:\n{e.__class__.__name__}\nMessage:\n{e.message}'
        else:
            msg = str(e)

        sg.popup_error(msg, title="uh oh")

if __name__ == "__main__":
    main()