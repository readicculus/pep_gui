import base64
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

class UserProperties:
    def __init__(self):
        self.settings = get_user_settings()

    def refresh(self):
        self.settings = get_user_settings()

    @property
    def viame_dir(self):
        return self.settings.get(SystemSettingsNames.viame_directory, None)

    @property
    def data_manifest_filepath(self):
        return self.settings.get(SystemSettingsNames.dataset_manifest_filepath, None)

    @property
    def job_base_dir(self):
        return self.settings.get(SystemSettingsNames.job_directory, None)

    def as_dict(self):
        return {'viame_dir': self.viame_dir,
                'data_manifest_filepath':self.data_manifest_filepath,
                'job_base_dir': self.job_base_dir}



WINDOW_ICON = image_resource_path('icon_tiny.png')
icon = base64.b64encode(open(WINDOW_ICON, 'rb').read())
sg.set_options(icon=icon, titlebar_icon=icon)