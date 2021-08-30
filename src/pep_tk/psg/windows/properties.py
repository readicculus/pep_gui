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

# https://github.com/PySimpleGUI/PySimpleGUI/issues/3058
import abc
import os
import PySimpleGUI as sg
from dataclasses import dataclass

from pep_tk.core.parser.load_dataset import safe_load_dataset_manifest
from pep_tk.psg.settings import get_user_settings, SystemSettingsNames, get_viame_bash_or_bat_file_path, UserProperties


def xstr(s):
    if s is None:
        return ''
    return str(s)


class Validator(metaclass=abc.ABCMeta):
    input_key = None

    @abc.abstractmethod
    def validate_ui(self, window: sg.Window) -> bool:
        pass

    @abc.abstractmethod
    def validate(self, v) -> bool:
        pass

    def value(self, window: sg.Window):
        return os.path.normpath(xstr(window[self.input_key].get()))

    def update_error(self, window: sg.Window, message=None):
        if message:
            window[self.input_key].update(text_color='red')
            sg.popup_no_buttons(message, title="Properties Error", keep_on_top=True, modal=True,
                                location=window.current_location())
        else:
            window[self.input_key].update(text_color='black')
        return False


class DataManifestValidator(Validator):
    input_key = '-dataset_manifest_filepath-IN-'

    def validate_ui(self, window: sg.Window) -> bool:
        if window[self.input_key].get() == "":
            return False
        dm, error = safe_load_dataset_manifest(self.value(window))
        self.update_error(window, error)
        return error is None

    def validate(self, v) -> bool:
        if v is None or v == '':
            return False
        dm, error = safe_load_dataset_manifest(v)
        return error is None


class JobBaseDirValidator(Validator):
    input_key = '-job_dir-IN-'

    def validate_ui(self, window: sg.Window) -> bool:
        if window[self.input_key].get() == "":
            return False
        error = None
        val = self.value(window)
        if not os.path.isdir(val):
            error = f'Job directory "{val}" does not exist.'
        self.update_error(window, error)
        return error is None

    def validate(self, v) -> bool:
        if v is None or v == '':
            return False
        return os.path.isdir(v)


class VIAMEDirValidator(Validator):
    input_key = '-setup_viame_filepath-IN-'

    def validate_ui(self, window: sg.Window) -> bool:
        if window[self.input_key].get() == "":
            return False
        error = None
        setup_viame_fp = get_viame_bash_or_bat_file_path(self.value(window))
        if not os.path.isfile(setup_viame_fp):
            error = f'Invalid VIAME/SEAL-TK directory.  ' \
                    f'Was unable to find setup_viame.sh(linux) or setup_viame.bat(windows) in the selected directory ' \
                    f'{setup_viame_fp}.',

        self.update_error(window, error)
        return error is None

    def validate(self, v) -> bool:
        if v is None or v == '':
            return False
        setup_viame_fp = get_viame_bash_or_bat_file_path(v)
        return os.path.isfile(setup_viame_fp)


dm_validator = DataManifestValidator()
viame_validator = VIAMEDirValidator()
jobdir_validator = JobBaseDirValidator()

@dataclass
class PropertiesWindowOutput:
    dm_valid: bool
    job_valid: bool
    viame_valid: bool
    properties_updated: bool = None

    @property
    def all_valid(self):
        return all([self.dm_valid, self.job_valid, self.viame_valid])

def check_inputs(window: sg.Window, update=True) -> PropertiesWindowOutput:
    d_valid = dm_validator.validate_ui(window)
    v_valid = viame_validator.validate_ui(window)
    j_valid = jobdir_validator.validate_ui(window)
    if update:
        user_settings = get_user_settings()
        if d_valid:
            user_settings[SystemSettingsNames.dataset_manifest_filepath] = dm_validator.value(window)

        if j_valid:
            user_settings[SystemSettingsNames.job_directory] = jobdir_validator.value(window)

        if v_valid:
            user_settings[SystemSettingsNames.viame_directory] = viame_validator.value(window)

    return PropertiesWindowOutput(dm_valid=d_valid, viame_valid=v_valid, job_valid=j_valid)


def check_settings():
    p = UserProperties()
    d_valid = dm_validator.validate(p.data_manifest_filepath)
    v_valid = viame_validator.validate(p.viame_dir)
    j_valid = jobdir_validator.validate(p.job_base_dir)
    out = PropertiesWindowOutput(dm_valid=d_valid, job_valid=j_valid, viame_valid=v_valid)
    return out

def show_properties_window(skip_if_valid=False, modal=True) -> PropertiesWindowOutput:
    """

    :param skip_if_valid:
    :param modal:
    :param error_message:
    :return: true if settings were updated, false if not
    """
    out = check_settings()
    if out.all_valid and skip_if_valid:
        out.properties_updated = False
        return out

    p = UserProperties()
    settings_before = p.as_dict()
    def properties_changed() -> bool:
        p.refresh()
        return p.as_dict() != settings_before

    manifest_folder = os.path.dirname(p.data_manifest_filepath) if p.data_manifest_filepath else None
    layout = [[sg.Text('Enter the viame directory:')],
              [sg.Input(xstr(p.viame_dir), key=VIAMEDirValidator.input_key),
               sg.FolderBrowse(initial_folder=p.viame_dir)],

              [sg.Text('Enter the dataset manifest filepath:')],
              [sg.Input(xstr(p.data_manifest_filepath), key=DataManifestValidator.input_key),
               sg.FileBrowse(initial_folder=manifest_folder)],

              [sg.Text('Enter the job base directory(directory where all jobs go):')],
              [sg.Input(xstr(p.job_base_dir), key=JobBaseDirValidator.input_key),
               sg.FolderBrowse(initial_folder=p.job_base_dir)],

              [sg.B('Complete Setup'), sg.B('Exit', key='Exit')]]

    user_settings = get_user_settings()
    location = user_settings[SystemSettingsNames.window_location] or (0, 0)
    window = sg.Window('PEP-TK: Properties',
                       layout,
                       keep_on_top=True,
                       finalize=True,
                       location=location,
                       modal=modal)

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            out = check_settings()
            out.properties_updated = False
            window.close()
            return out
        elif event == 'Complete Setup':
            out = check_inputs(window)
            out.properties_updated = properties_changed()
            if out.all_valid:
                window.close()
                return out

