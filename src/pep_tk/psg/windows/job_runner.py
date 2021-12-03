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

import datetime
import threading
import time
from typing import List

import PySimpleGUI as sg

from pep_tk.core.job import load_job, TaskStatus, TaskKey
from pep_tk.core.scheduler import Scheduler
from pep_tk.psg.events import GUIManager
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import TaskTab, TaskRunnerTabGroup
from pep_tk.psg.settings import get_user_settings, SystemSettingsNames, get_viame_bash_or_bat_file_path
from pep_tk.psg.utils import set_pep_theme

set_pep_theme(sg)



def make_main_window(tasks: List[TaskKey], gui_settings: sg.UserSettings):
    tabs = [TaskTab(task_key) for task_key in tasks]
    tabs_group = TaskRunnerTabGroup([(t.get_layout(), t.task_key) for t in tabs])
    header = sg.Frame(title='', layout=[[sg.Text('Job Progress:', font=Fonts.title_medium)],
              [sg.Text('xxxxxxx/xxxxxxx images or XX.XX% complete.', key='--total-progress-ta--')]], expand_x=True)
    layout = [[header],
              [tabs_group.get_layout()]]

    location = gui_settings.get(SystemSettingsNames.window_location, (0, 0))
    window = sg.Window('PEP-TK: Job Runner', layout, location=location, finalize=True,
                       enable_close_attempted_event=True, use_default_focus=False)

    window['-progress-frame-'].expand(True, True, True)
    tabs_group.select_tab(window)  # ensure first tab is selected

    return window, tabs, tabs_group


def run_job(job_path: str):
    user_settings = get_user_settings()
    job_state, job_meta = load_job(job_path)

    window, tabs, tabs_group = make_main_window(job_state.tasks(), user_settings)
    tabs_by_update_key = {t.task_progress_update_key: t for t in tabs}
    manager = GUIManager(window=window, tabs=tabs)
    kill_event = threading.Event()
    sched = Scheduler(job_state=job_state,
                      job_meta=job_meta,
                      manager=manager,
                      kwiver_setup_path=get_viame_bash_or_bat_file_path(
                          user_settings.get(SystemSettingsNames.viame_directory)), kill_event=kill_event)

    threading.Thread(target=sched.run, daemon=True).start()

    def update_total_progress(window: sg.Window, start_time: int):
        total_progress = 0
        total = 0
        completed_on_load_count = 0
        for tab in tabs:
            total += tab.max_count
            if tab.status == TaskStatus.SUCCESS:
                total_progress += tab.max_count
                if tab.completed_on_load:
                    completed_on_load_count += tab.max_count
            else:
                total_progress += tab.progress_count

        total_completed_items = total_progress - completed_on_load_count
        elapsed_time = time.time() - start_time
        if total_completed_items == 0:
            time_per_epoch = 0
        else:
            time_per_epoch = elapsed_time / total_completed_items

        remaining_time = (total - total_progress) * time_per_epoch
        percent = (total_progress/total) * 100

        elapsed_str = str(datetime.timedelta(seconds=int(elapsed_time)))
        remaining_str = str(datetime.timedelta(seconds=int(remaining_time)))

        window['--total-progress-ta--'].update(value=f'{total_progress}/{total} items({percent:.2f}%) complete.  {time_per_epoch:.2f} seconds/iter.  '
                                                     f'Elapsed time {elapsed_str}. Estimated time remaining {remaining_str}.')

    start_time = time.time()
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
                kill_event.set()
                window.close()
                break
        else:
            if event in tabs_by_update_key:
                tabs_by_update_key[event].handle(window, event, values)
                update_total_progress(window, start_time)

            tabs_group.handle(window, event, values)

