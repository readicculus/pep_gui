
# Given a job directory, load the job and start/resume running
from core.job import load_job, JobMeta, JobState
from core.scheduler import Scheduler, SchedulerEventManager
from initial_setup import initial_setup
from layouts.layout import LayoutSection
from settings import get_settings, SettingsNames, get_viame_bash_or_bat_file_path
import PySimpleGUI as sg

sg.theme('SystemDefaultForReal')

def progress_meter_gui_key(task_key):
    return f'--progress-bar-{task_key}--'

def progress_meter_layout(task_key):
    return [sg.T(task_key), sg.ProgressBar(1, orientation='hs', size=(20, 20), key=progress_meter_gui_key(task_key))]



class BetterProgressBar(LayoutSection):
    def __init__(self, task_key, job_meta: JobMeta):
        self.task_key = task_key
        pipeline_fp, dataset, outputs = job_meta.get(task_key)

    def get_layout(self):
        title = sg.T(self.task_key)
        pb = sg.ProgressBar(1, orientation='hs', size=(20, 20), key=self.pb_key)
        time_elapsed_remaining = sg.T('', key=self.elapsed_key, size=(1,8)) # size of time 00:00:00
        counter = sg.T('00000/00000', key=self.counter_key)
        return [title, pb, time_elapsed_remaining, counter]

    def handle(self, window, event, values):
        if event in self.event_keys():
            pass

    def event_keys(self):
        return [self.pb_key, self.elapsed_key, self.counter_key]

    @property
    def pb_key(self):
        return f'--progress-bar-{self.task_key}--'

    @property
    def elapsed_key(self):
        return f'--elapsed-{self.task_key}--'

    @property
    def counter_key(self):
        return f'--counter-{self.task_key}--'

    @property
    def layout_name(self) -> str:
        return self.task_key

class GUIManager(SchedulerEventManager):

    def task_started(self, task_key):
        print('task_started')

    def task_finished(self, task_key):
        print('task_finished')

    def task_update_progress(self, task_key, progress):
        print('task_update_progress')

    def task_update_stdout(self, task_key, log: str):
        print('task_update_stdout(%s): %s' % (task_key, log))


def run_job(job_path: str):
    # initial_setup(skip_if_complete=False)

    gui_settings = get_settings()
    job_state, job_meta = load_job(job_path)
    manager = GUIManager(settings=gui_settings)

    sched = Scheduler(job_state, job_meta, manager)
    sched.run()

    meters = []
    for task_key in job_state.tasks():
        meters.append(progress_meter_layout(task_key))

    layout = [[sg.Text('A typical custom progress meter')],
              meters,
              [sg.Cancel()]]

    location = (0, 0)
    if SettingsNames.window_location in gui_settings.get_dict():
        location = gui_settings[SettingsNames.window_location]

    window = sg.Window('GUI', layout,
                       default_element_size=(12, 1), location=location)
    while True:
        event, values = window.read()
        # sg.popup_non_blocking(event,  values)
        print(event, values)
        if event == sg.WIN_CLOSED:  # always,  always give a way out!
            break

if __name__ == '__main__':
    # TODO: open job selection GUI
    run_job('/home/yuval/Desktop/jobs/test')