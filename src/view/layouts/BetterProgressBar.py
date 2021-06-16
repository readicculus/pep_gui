import datetime

import PySimpleGUI as sg
from dataclasses import dataclass

from pep_tk.core.job import TaskStatus
from view.layouts import LayoutSection
from view.settings import image_resource_path


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

    @property
    def estimated_time_remaining(self) -> float:
        return self.time_per_count * (self.max_count - self.progress_count)


status_icons = {TaskStatus.SUCCESS: image_resource_path('status_success.png'),
                TaskStatus.ERROR: image_resource_path('status_error.png'),
                TaskStatus.RUNNING: image_resource_path('status_running.png')}


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
        self._status_key = f'--bpb-status-{self.task_key}--'

    def get_layout(self):
        def empty_string(s):
            return ' ' * len(s)

        status_icon = sg.Image(size=(24, 24), key=self._status_key)
        title = sg.T(self.task_key, size=(len(self.task_key), 1), key=self._text_title_key)
        pb = sg.ProgressBar(100, orientation='hs', size=(20, 4), key=self._pb_key)
        elapsed_str = empty_string('00:00:00 elapsed 00:00:00 remaining')
        time_elapsed = sg.T(elapsed_str, key=self._elapsed_key)
        counter_str = empty_string('00000/00000')
        counter = sg.T(counter_str, key=self._counter_key)
        iter_str = empty_string('x.xx seconds/iter')
        avg_iteration_time = sg.T(iter_str, key=self._iteration_time_key, size=(len('x.xx seconds/iter'), 1))
        return [status_icon, title, pb, time_elapsed, counter, avg_iteration_time]

    def handle(self, window, event, values):
        if event != self.task_progress_update_key:
            return

        progress: ProgressGUIEventData = values[event]
        self._update_avg_iteration_time(window, progress.time_per_count)
        self._update_time_elapsed(window, progress.elapsed_time, progress.estimated_time_remaining)
        self._update_pb(window, progress.progress_count, progress.max_count)
        self._update_counter(window, progress.progress_count, progress.max_count)
        self._update_status(window, progress.task_status)

    def _update_status(self, window: sg.Window, status: TaskStatus):
        window[self._status_key].update(filename=status_icons.get(status, None))
        pass  # TODO

    def _update_avg_iteration_time(self, window: sg.Window, avg_iteration_time: float):
        fmt = '%.2f seconds/iter' % avg_iteration_time
        window[self._iteration_time_key](value=fmt)

    def _update_time_elapsed(self, window: sg.Window, elapsed_time: float, remaining_time: float):
        elapsed = str(datetime.timedelta(seconds=int(elapsed_time)))
        remaining = str(datetime.timedelta(seconds=int(remaining_time)))
        v = '%s elapsed %s remaining' % (elapsed, remaining)
        window[self._elapsed_key](value=v)

    def _update_pb(self, window: sg.Window, count: int, max_count: int):
        window[self._pb_key].update_bar(count, max_count)

    def _update_counter(self, window: sg.Window, count: int, max_count: int):
        window[self._counter_key](value='%d/%d' % (count, max_count))

    def layout_name(self) -> str:
        return self.task_progress_update_key
