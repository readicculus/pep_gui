import datetime

import PySimpleGUI as sg
from dataclasses import dataclass

from core.job import TaskStatus
from layouts.layout import LayoutSection


@dataclass
class ProgressGUIEventData:
    """ Data message communicated between the Scheduler thread and the main GUI thread """
    progress_count: int  # number of items processed already in task
    max_count: int  # number of items being processed in task
    elapsed_time: float  # time elapsed so far
    task_status: TaskStatus  # current status of the task

    @property
    def time_per_count(self) -> float:  # average time taken to process each item
        if self.progress_count == 0:
            return 0
        return self.elapsed_time / self.progress_count


class BetterProgressBar(LayoutSection):
    """
        A better progress bar than the default PySimpleGUI Progress Bar
        - Worker thread triggers a window even, passing a ProgressGUIEventData object to the GUI with
          the task_progress_update_key as the event key.
        - This then updates the BetterProgressBar with that task_progress_update_key
        - Contains information on elapsed time, a progress counter, avg time/iteration, and task name
     """
    def __init__(self, task_key):
        self.task_key = task_key

        # globally used key for triggering an update for a task's BetterProgressBar GUI layout
        self.task_progress_update_key = f'--bpb-update-{self.task_key}--'

        # GUI element keys
        self._text_title_key = f'--bpb-text-title-{self.task_key}--'
        self._pb_key = f'--bpb-progress-bar-{self.task_key}--'
        self._elapsed_key = f'--bpb-elapsed-{self.task_key}--'
        self._counter_key = f'--bpb-counter-{self.task_key}--'
        self._iteration_time_key = f'--bpb-iteration-time-{self.task_key}--'

    def get_layout(self):
        title = sg.T(self.task_key, size=(len(self.task_key), 1), key=self._text_title_key)
        pb = sg.ProgressBar(100, orientation='hs', size=(20, 4), key=self._pb_key)
        time_elapsed_remaining = sg.T('00:00:00', key=self._elapsed_key)  # size of time 00:00:00
        counter = sg.T('00000/00000', key=self._counter_key, size=(len('00000/00000'), 1))
        avg_iteration_time = sg.T('x.xx seconds/iter', key=self._iteration_time_key, size=(len('x.xx seconds/iter'), 1))
        return [title, pb, time_elapsed_remaining, counter, avg_iteration_time]

    def handle(self, window, event, values):
        if event != self.task_progress_update_key:
            return

        progress: ProgressGUIEventData = values[event]
        self._update_avg_iteration_time(window, progress.time_per_count)
        self._update_time_elapsed(window, progress.elapsed_time)
        self._update_pb(window, progress.progress_count, progress.max_count)
        self._update_counter(window, progress.progress_count, progress.max_count)
        self._update_status(window, progress.task_status)

    def _update_status(self, window: sg.Window, status: TaskStatus):
        pass  # TODO

    def _update_avg_iteration_time(self, window: sg.Window, avg_iteration_time: float):
        fmt = '%.2f seconds/iter' % avg_iteration_time
        window[self._iteration_time_key](value=fmt)

    def _update_time_elapsed(self, window: sg.Window, elapsed_time: float):
        td = datetime.timedelta(seconds=elapsed_time)
        window[self._elapsed_key](value=str(td))

    def _update_pb(self, window: sg.Window, count: int, max_count: int):
        window[self._pb_key].update_bar(count, max_count)

    def _update_counter(self, window: sg.Window, count: int, max_count: int):
        window[self._counter_key](value='%d/%d' % (count, max_count))

    def layout_name(self) -> str:
        return self.task_progress_update_key
