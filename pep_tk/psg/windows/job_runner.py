import threading
from typing import List, Dict

import PySimpleGUI as sg
from dataclasses import dataclass

from pep_tk.core.job import load_job, TaskStatus, TaskKey
from pep_tk.core.scheduler import Scheduler, SchedulerEventManager
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import TaskTab, TaskRunnerTabGroup, ProgressGUIEventData
from pep_tk.psg.settings import get_user_settings, SystemSettingsNames, get_viame_bash_or_bat_file_path

sg.theme('SystemDefaultForReal')

class GUIManager(SchedulerEventManager):
    def __init__(self, window: sg.Window, tabs: List[TaskTab]):
        super().__init__()
        self._window = window
        self._progress_bars: Dict[TaskKey, TaskTab] = {t.task_key: t for t in tabs}
        self.stdout = {}
        self.stderr = {}

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
                                        elapsed_time=self.elapsed_time(task_key),
                                        output_log=self.pop_stdout(task_key))
        self._window.write_event_value(gui_task_event_key, evt_data)
        # delete outputs from memory when task is finished
        if task_key in self.stdout:
            del self.stdout[task_key]
        if task_key in self.stderr:
            del self.stderr[task_key]
        print('task_finished')

    def _update_task_progress(self, task_key: TaskKey, current_count: int, max_count: int):
        evt_data = ProgressGUIEventData(task_status=self.task_status[task_key],
                                        progress_count=self.task_count[task_key],
                                        max_count=self.task_max_count[task_key],
                                        elapsed_time=self.elapsed_time(task_key),
                                        output_log=self.pop_stdout(task_key))

        gui_task_event_key = self.task_event_key(task_key)
        self._window.write_event_value(gui_task_event_key, evt_data)
        print('task_update_progress')

    def pop_stdout(self, task_key) -> str:
        stdout = self.stdout.get(task_key, None)
        self.stdout[task_key] = ""
        return stdout

    def _update_task_stdout(self, task_key: TaskKey, line: str):
        if task_key not in self.stdout:
            self.stdout[task_key] = ""
        self.stdout[task_key] += line
        # print('task_update_stdout(%s): %s' % (task_key, line))
        # evt_data = ProgressGUIEventData(output_log=self.pop_stdout(task_key))
        #
        # gui_task_event_key = self.task_event_key(task_key)
        # self._window.write_event_value(gui_task_event_key, evt_data)

    def _update_task_stderr(self, task_key: TaskKey, line: str):
        if task_key not in self.stderr:
            self.stderr[task_key] = ""
        self.stderr[task_key] += line
        # print('task_update_stderr(%s): %s' % (task_key, line))

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
    tabs = [TaskTab(task_key) for task_key in tasks]
    # progress_bars = {tab.task_progress_update_key: tab for tab in tabs}

    tabs_group = TaskRunnerTabGroup([(t.get_layout(), t.task_key) for t in tabs])
    layout = [[sg.Text('Job Progress:', font=Fonts.title_medium)],
              [tabs_group.get_layout()]]

    location = gui_settings.get(SystemSettingsNames.window_location, (0, 0))
    window = sg.Window('PEP-TK: Job Runner', layout, location=location, finalize=True,
                       enable_close_attempted_event=True, use_default_focus=False)

    window['-progress-frame-'].expand(True, True, True)
    tabs_group.select_tab(window) # ensure first tab is selected

    return window, tabs, tabs_group


def run_job(job_path: str):
    user_settings = get_user_settings()
    job_state, job_meta = load_job(job_path)

    window, tabs, tabs_group = make_main_window(job_state.tasks(), user_settings)
    tabs_by_update_key = {t.task_progress_update_key: t for t in tabs}
    manager = GUIManager(window=window, tabs=tabs)
    sched = Scheduler(job_state=job_state,
                      job_meta=job_meta,
                      manager=manager,
                      kwiver_setup_path=get_viame_bash_or_bat_file_path(
                          user_settings.get(SystemSettingsNames.viame_directory)))

    threading.Thread(target=sched.run, daemon=True).start()

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            window.close()
            break
        elif event == sg.WIN_X_EVENT:
            # If user tries to close the window by clicking X, show a popup asking to confirm the action.
            try:
                location = window.current_location()
            except:
                location = (None, None)
            res = sg.popup_ok_cancel("Closing this window will stop any active tasks, "
                                     "are you sure you want to close?",
                                     title='Are you sure?', location=location)
            if res == 'OK':
                window.close()
                break
        else:
            if event in tabs_by_update_key:
                tabs_by_update_key[event].handle(window, event, values)
            tabs_group.handle(window, event, values)

if __name__ == '__main__':
    run_job('/home/yuval/Desktop/jobs/testa')