import PySimpleGUI as sg

class SettingsNames:
    setup_viame_filepath = 'setup_viame_filepath'
    dataset_manifest_filepath = 'dataset_manifest_filepath'
    window_location = 'window_location'
    job_directory = 'job_directory'


def get_settings():
    return sg.UserSettings(filename='peptk_gui_settings.json')

