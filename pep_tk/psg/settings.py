import os
import PySimpleGUI as sg
from pep_tk import PLUGIN_PATH

class SystemSettingsNames:
    viame_directory = 'setup_viame_filepath'
    dataset_manifest_filepath = 'dataset_manifest_filepath'
    window_location = 'window_location'
    recent_jobs_list = 'recent_jobs_list'
    detection_output_location = 'detection_output_location'
    job_directory = 'job_directory'

def image_resource_path(file_path=''):
    return os.path.join(PLUGIN_PATH, 'lib', 'img', file_path)

# filename of icon and '1x' or '2x' for size
def icon_filepath(icon_fn, size='1x'):
    assert (size == '1x' or size == '2x')
    return os.path.normpath(os.path.join(PLUGIN_PATH, 'lib', 'img', 'icons', size, icon_fn))

def system_settings_filepath():
    return os.path.normpath(os.path.join(PLUGIN_PATH, 'peptk_gui_settings.json'))

def get_system_settings():
    return sg.UserSettings(filename=system_settings_filepath())

def get_user_settings():
    return sg.UserSettings(filename='peptk_gui_settings.json')

def get_viame_bash_or_bat_file_path(viame_dir):
    if os.name == 'nt':
        fn = 'setup_viame.bat'
    else:
        fn = 'setup_viame.sh'

    return os.path.normpath(os.path.join(viame_dir, fn))

WINDOW_ICON = image_resource_path('bear.png')
