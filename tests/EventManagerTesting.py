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
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from pep_tk.psg.events import ProgressGUIEventData
from util import add_src_to_pythonpath

add_src_to_pythonpath()

from pep_tk.core.scheduler import SchedulerEventManager
from pep_tk.core.job import TaskKey, TaskStatus



@dataclass
class TestProgressGUIEventData(ProgressGUIEventData):
    ts: float = field(default_factory=lambda: datetime.now().timestamp())


# The Event Manager used for testing
class EventManagerTesting(SchedulerEventManager):
    def __init__(self, tasks: List[TaskKey]):
        super().__init__()
        self.tasks = tasks
        self.task_events = {task_key: [] for task_key in tasks}
        self.stdout = {}
        self.stderr = {}

    def _initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus):
        evt_data = TestProgressGUIEventData(task_status=self.task_status[task_key],
                                            progress_count=count,
                                            max_count=max_count,
                                            elapsed_time=self.elapsed_time(task_key),
                                            completed_on_load=self.task_status[task_key] == TaskStatus.SUCCESS,
                                            output_log=self.pop_stdout(task_key, min_lines_to_pop=0))

        self.task_events[task_key].append(('_initialize_task', evt_data))

    def _check_cancelled(self, task_key: TaskKey) -> bool:
        self.task_events[task_key].append(('_check_cancelled', None))
        return self.task_status[task_key] == TaskStatus.CANCELLED

    def _start_task(self, task_key: TaskKey):
        self.task_events[task_key].append(('_start_task', None))

    def _end_task(self, task_key: TaskKey, status: TaskStatus):
        evt_data = TestProgressGUIEventData(task_status=status,
                                            progress_count=self.task_count[task_key],
                                            max_count=self.task_max_count[task_key],
                                            elapsed_time=self.elapsed_time(task_key),
                                            output_log=self.pop_stdout(task_key, min_lines_to_pop=0))
        self.task_events[task_key].append(('_end_task', evt_data))

    def _update_task_progress(self, task_key: TaskKey, current_count: int, max_count: int):
        evt_data = TestProgressGUIEventData(task_status=self.task_status[task_key],
                                            progress_count=self.task_count[task_key],
                                            max_count=self.task_max_count[task_key],
                                            elapsed_time=self.elapsed_time(task_key),
                                            output_log=self.pop_stdout(task_key, min_lines_to_pop=5))
        self.task_events[task_key].append(('_update_task_progress', evt_data))

    def _update_task_stdout(self, task_key: TaskKey, line: str):
        if task_key not in self.stdout:
            self.stdout[task_key] = []
        self.stdout[task_key].append(line)

    def _update_task_stderr(self, task_key: TaskKey, line: str):
        if task_key not in self.stderr:
            self.stderr[task_key] = ""
        self.stderr[task_key] += line

    def _update_task_output_files(self, task_key: TaskKey, output_files: List[str]):
        evt_data = TestProgressGUIEventData(task_status=self.task_status[task_key],
                                            progress_count=self.task_count[task_key],
                                            max_count=self.task_max_count[task_key],
                                            elapsed_time=self.elapsed_time(task_key),
                                            output_files=output_files)
        self.task_events[task_key].append(('_update_task_output_files', evt_data))

    def pop_stdout(self, task_key, min_lines_to_pop=50) -> Optional[str]:
        # pass
        out = self.stdout.get(task_key)
        if not out:
            return None
        if len(out) > min_lines_to_pop:
            self.stdout[task_key] = []
            return ''.join(out)
        return None

    def get_events_with_eventdata(self, task_key) -> List[Tuple[str, TestProgressGUIEventData]]:
        events = self.task_events.get(task_key)
        if not events:
            return []
        res = []
        for event_name, event_data in events:
            if event_data:
                res.append((event_name, event_data))

        return res

    def get_events_by_type(self, task_key, type: str) -> List[Tuple[str, TestProgressGUIEventData]]:
        events = self.task_events.get(task_key)
        if not events:
            return []
        res = []
        for event_name, event_data in events:
            if event_name == type:
                res.append((event_name, event_data))

        return res

    def get_full_log(self, task_key):
        log = ""
        for name, val in self.get_events_with_eventdata(task_key):
            if val.output_log:
                log += val.output_log
        return log