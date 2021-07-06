import os

import PySimpleGUI as sg

from pep_tk import PLUGIN_PATH


class SettingsNames:
    setup_viame_filepath = 'setup_viame_filepath'
    dataset_manifest_filepath = 'dataset_manifest_filepath'
    window_location = 'window_location'
    job_directory = 'job_directory'
    recent_jobs_list = 'recent_jobs_list'

def image_resource_path(file_path =''):
    # abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib/img/'))
    return os.path.join(PLUGIN_PATH, 'lib', 'img', file_path)

def get_settings():
    return sg.UserSettings(filename='peptk_gui_settings.json')

def get_viame_bash_or_bat_file_path(settings: sg.UserSettings):
    base_dir = settings[SettingsNames.setup_viame_filepath]
    if os.name == 'nt':
        fn = 'setup_viame.bat'
    else:
        fn = 'setup_viame.sh'

    return os.path.join(base_dir, fn)

class JobCache:
    def __init__(self, settings: sg.UserSettings):
        self.settings = settings
        self.jobs = set()
        # get recent jobs from settings and only add if the job folder still exists
        for job in settings.get(SettingsNames.recent_jobs_list, []):
            if os.path.isdir(job):
                self.jobs.add(job)
        self.jobs = list(self.jobs)

    def get_jobs(self, max_count: int = 0):
        if max_count == 0 or max_count > len(self.jobs):
            return self.jobs
        return self.jobs[:max]

    def append_job(self, job_dir: str):
        self.jobs.append(job_dir)
        if SettingsNames.recent_jobs_list not in self.settings:
            self.settings[SettingsNames.recent_jobs_list] = []
        self.settings[SettingsNames.recent_jobs_list].append(job_dir)

    def remove_job(self, job_dir: str):
        pass

    def clear_all(self):
        self.settings[SettingsNames.recent_jobs_list] = []
        self.jobs = []


WINDOW_ICON = image_resource_path('bear.png')
