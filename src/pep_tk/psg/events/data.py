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
from dataclasses import dataclass
from typing import List, Optional

from pep_tk.core.job import TaskStatus


@dataclass
class ProgressGUIEventData:
    """ Data message communicated between the Scheduler thread and the main GUI thread """
    progress_count: int = None  # number of items processed already in task
    max_count: int = None  # number of items being processed in task
    elapsed_time: float = None  # time elapsed so far
    task_status: TaskStatus = None  # current status of the task
    output_files: List[str] = None  # output files from the task (image lists, detections)
    output_log: str = None
    completed_on_load: bool = False # if task was already completed when initialized/loaded

    @property
    def time_per_count(self) -> float:  # average time taken to process each item
        if self.progress_count == None:
            return 0
        if self.progress_count == 0:
            return 0
        return self.elapsed_time / self.progress_count

    @property
    def estimated_time_remaining(self) -> Optional[float]:
        if self.progress_count == None or self.max_count == None:
            return None
        return self.time_per_count * (self.max_count - self.progress_count)