import PySimpleGUI as sg

from core.job import JobState


class SettingsNames:
    setup_viame_filepath = 'setup_viame_filepath'
    dataset_manifest_filepath = 'dataset_manifest_filepath'
    window_location = 'window_location'
    job_directory = 'job_directory'
    job_cache = 'job_list_cache'


def get_settings():
    return sg.UserSettings(filename='peptk_gui_settings.json')

def add_job_directory(settings: sg.UserSettings, job_state: JobState):
    if SettingsNames.job_cache not in settings:
        settings[SettingsNames.job_cache] = {}

    settings[SettingsNames.job_cache] = {}
