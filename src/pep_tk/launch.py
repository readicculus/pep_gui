import os
import sys

def main():
    from pep_tk.core.parser import load_dataset_manifest, DatasetManifestError, EmptyParser
    from pep_tk.psg.settings import UserProperties
    from pep_tk.psg.windows import launch_gui, popup_error
    from pep_tk.core.configuration import PipelineManifest
    success = False
    while not success:
        # launch_gui returns False if needs to be refreshed, returns true if program exits
        pm = PipelineManifest()
        try:
            p = UserProperties()
            dm = load_dataset_manifest(p.data_manifest_filepath)
        except DatasetManifestError as e:
            # Handeled dataset manifest exception on startup - pass an empty dataset manifest
            if hasattr(e, 'message'):
                msg = f'Error Type: {e.__class__.__name__}\nMessage:\n{e.message}'
            else:
                msg = str(e)
            dm = EmptyParser(error_message=msg)
        except Exception as e:
            # Unhandled exception on startup - show error and end application
            if hasattr(e, 'message'):
                msg = f'Unhandled Error Contact Yuval!\nError Type:\n{e.__class__.__name__}\nMessage:\n{e.message}'
            else:
                msg = str(e)

            popup_error(msg)
            return

        success = launch_gui(pm, dm)


if __name__ == "__main__":
    PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    plugin_python_lib = os.path.join(PLUGIN_PATH, 'lib', 'python3.6', 'site-packages')
    sys.path.insert(0, plugin_python_lib)
    print('Added %s to PYTHONPATH' % plugin_python_lib)

    main()
