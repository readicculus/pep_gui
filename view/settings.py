import os

import PySimpleGUI as sg

class SettingsNames:
    setup_viame_filepath = 'setup_viame_filepath'
    dataset_manifest_filepath = 'dataset_manifest_filepath'
    window_location = 'window_location'
    job_directory = 'job_directory'
    job_cache = 'job_list_cache'

def image_resource_path(file_path =''):
    abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/img/'))
    return os.path.join(abspath, file_path)

def get_settings():
    return sg.UserSettings(filename='peptk_gui_settings.json')

def get_viame_bash_or_bat_file_path(settings: sg.UserSettings):
    base_dir = settings[SettingsNames.setup_viame_filepath]
    if os.name == 'nt':
        fn = 'setup_viame.bat'
    else:
        fn = 'setup_viame.sh'

    return os.path.join(base_dir, fn)

WINDOW_ICON = image_resource_path('bear.png')
