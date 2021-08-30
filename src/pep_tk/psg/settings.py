#      This file is part of the PEP GUI detection pipeline batch running tool
#      Copyright (C) 2021 Yuval Boss yuval@uw.edu
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import base64
import os
import PySimpleGUI as sg
from pep_tk import PLUGIN_PATH
from pep_tk.psg.fonts import Fonts


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
    """ This class represents all of the properties in the settings file that the user has control over, and
     are able to set through the Properties window in the GUI. """
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
                'data_manifest_filepath': self.data_manifest_filepath,
                'job_base_dir': self.job_base_dir}


WINDOW_ICON = image_resource_path('icon_80x80.png')
with open(WINDOW_ICON, 'rb') as f:
    icon = base64.b64encode(f.read())
sg.set_options(icon=icon, titlebar_icon=icon, font=Fonts.description)
