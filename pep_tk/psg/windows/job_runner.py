# Given a job directory, load the job and start/resume running
import threading
from typing import List, Dict

import PySimpleGUI as sg

from pep_tk.core.job import load_job, TaskStatus, TaskKey
from pep_tk.core.scheduler import Scheduler, SchedulerEventManager
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import TaskTab, ProgressGUIEventData
from pep_tk.psg.settings import get_settings, SettingsNames, get_viame_bash_or_bat_file_path
from pep_tk.psg.layouts import TaskRunnerTabGroup

sg.theme('SystemDefaultForReal')


class GUIManager(SchedulerEventManager):
    def __init__(self, window: sg.Window, progress_bars):
        super().__init__()
        self._window = window
        self._progress_bars: Dict[TaskKey, TaskTab] = progress_bars

    def task_event_key(self, task_key: TaskKey):
        return self._progress_bars[task_key].task_progress_update_key

    def _initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus):
        evt_data = ProgressGUIEventData(task_status=self.task_status[task_key],
                                        progress_count=count,
                                        max_count=max_count,
                                        elapsed_time=self.elapsed_time(task_key))

        gui_task_event_key = self.task_event_key(task_key)
        self._window.write_event_value(gui_task_event_key, evt_data)
        print('task_initialized')

    def _check_cancelled(self, task_key: TaskKey):
        return self._progress_bars[task_key].is_cancelled

    def _start_task(self, task_key: TaskKey):
        print('task_started')

    def _end_task(self, task_key: TaskKey, status: TaskStatus):
        gui_task_event_key = self.task_event_key(task_key)
        evt_data = ProgressGUIEventData(task_status=status,
                                        progress_count=self.task_count[task_key],
                                        max_count=self.task_max_count[task_key],
                                        elapsed_time=self.elapsed_time(task_key))
        self._window.write_event_value(gui_task_event_key, evt_data)

        print('task_finished')

    def _update_task_progress(self, task_key: TaskKey, current_count: int, max_count: int):
        evt_data = ProgressGUIEventData(task_status=self.task_status[task_key],
                                        progress_count=self.task_count[task_key],
                                        max_count=self.task_max_count[task_key],
                                        elapsed_time=self.elapsed_time(task_key))

        gui_task_event_key = self.task_event_key(task_key)
        self._window.write_event_value(gui_task_event_key, evt_data)
        print('task_update_progress')

    def _update_task_stdout(self, task_key: TaskKey, line: str):
        print('task_update_stdout(%s): %s' % (task_key, line))

    def _update_task_stderr(self, task_key: TaskKey, line: str):
        pass

    def _update_task_output_files(self, task_key: TaskKey, output_files: List[str]):
        gui_task_event_key = self.task_event_key(task_key)
        evt_data = ProgressGUIEventData(task_status=self.task_status[task_key],
                                        progress_count=self.task_count[task_key],
                                        max_count=self.task_max_count[task_key],
                                        elapsed_time=self.elapsed_time(task_key),
                                        output_files=output_files)
        self._window.write_event_value(gui_task_event_key, evt_data)

        print('_update_task_output_files')


def make_main_window(tasks: List[TaskKey], gui_settings: sg.UserSettings):
    progress_bars = {task_key: TaskTab(task_key) for task_key in tasks}

    tabs = []
    for pb in list(progress_bars.values()):
        tabs.append((pb.get_layout(), pb.task_key))
    tabs_group = TaskRunnerTabGroup(tabs)
    layout = [[sg.Text('Job Progress:', font=Fonts.title_large)],
              [tabs_group.get_layout()]]

    location = gui_settings.get(SettingsNames.window_location, (0, 0))
    window = sg.Window('PEP-TK: Job Runner', layout, location=location, finalize=True)

    return window, progress_bars, tabs_group


def run_job(job_path: str):
    gui_settings = get_settings()
    job_state, job_meta = load_job(job_path)

    window, progress_bars, tabs_group = make_main_window(job_state.tasks(), gui_settings)

    manager = GUIManager(window=window, progress_bars=progress_bars)
    sched = Scheduler(job_state=job_state,
                      job_meta=job_meta,
                      manager=manager,
                      kwiver_setup_path=get_viame_bash_or_bat_file_path(gui_settings))

    threading.Thread(target=sched.run, daemon=True).start()

    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED:
            break

        for task_key, pb in progress_bars.items():
            pb.handle(window, event, values)
            tabs_group.handle(window, event, values)
