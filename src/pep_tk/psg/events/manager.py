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
from typing import List, Dict, Optional

import PySimpleGUI as sg

from pep_tk.core.job import TaskStatus, TaskKey
from pep_tk.core.scheduler import SchedulerEventManager
from pep_tk.psg.events.data import ProgressGUIEventData


class GUIManager(SchedulerEventManager):
    def __init__(self, window: sg.Window, tabs: List['TaskTab']):
        super().__init__()
        self._window = window
        self._task_tabs: Dict[TaskKey, 'TaskTab'] = {t.task_key: t for t in tabs}
        self.stdout = {}
        self.stderr = {}

    def task_event_key(self, task_key: TaskKey):
        return self._task_tabs[task_key].task_progress_update_key

    def _initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus):
        evt_data = ProgressGUIEventData(task_status=self.task_status[task_key],
                                        progress_count=count,
                                        max_count=max_count,
                                        elapsed_time=self.elapsed_time(task_key),
                                        completed_on_load=self.task_status[task_key] == TaskStatus.SUCCESS,
                                        output_log=self.pop_stdout(task_key, min_lines_to_pop=0))

        gui_task_event_key = self.task_event_key(task_key)
        self._window.write_event_value(gui_task_event_key, evt_data)
        print('task_initialized')

    def _check_cancelled(self, task_key: TaskKey):
        return self._task_tabs[task_key].is_cancelled

    def _start_task(self, task_key: TaskKey):
        print('task_started')

    def _end_task(self, task_key: TaskKey, status: TaskStatus):
        gui_task_event_key = self.task_event_key(task_key)
        evt_data = ProgressGUIEventData(task_status=status,
                                        progress_count=self.task_count[task_key],
                                        max_count=self.task_max_count[task_key],
                                        elapsed_time=self.elapsed_time(task_key),
                                        output_log=self.pop_stdout(task_key, min_lines_to_pop=0))
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
                                        output_log=self.pop_stdout(task_key, min_lines_to_pop=5))

        gui_task_event_key = self.task_event_key(task_key)
        self._window.write_event_value(gui_task_event_key, evt_data)
        print('task_update_progress')

    def pop_stdout(self, task_key, min_lines_to_pop=50) -> Optional[str]:
        out = self.stdout.get(task_key)
        if not out:
            return None
        if len(out) > min_lines_to_pop:
            self.stdout[task_key] = []
            return ''.join(out)
        return None

    def _update_task_stdout(self, task_key: TaskKey, line: str):
        if task_key not in self.stdout:
            self.stdout[task_key] = []
        self.stdout[task_key].append(line)

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
