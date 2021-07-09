import datetime
from typing import List, Optional

import PySimpleGUI as sg
from dataclasses import dataclass

from pep_tk.core.job import TaskStatus
from pep_tk.psg.layouts import LayoutSection
from pep_tk.psg.settings import image_resource_path, icon_filepath


def task_status_update_key(task_key):
    return f'--task-update-{task_key}--'


@dataclass
class ProgressGUIEventData:
    """ Data message communicated between the Scheduler thread and the main GUI thread """
    progress_count: int  # number of items processed already in task
    max_count: int  # number of items being processed in task
    elapsed_time: float  # time elapsed so far
    task_status: TaskStatus  # current status of the task
    output_files: List[str] = None  # output files from the task (image lists, detections)

    @property
    def time_per_count(self) -> float:  # average time taken to process each item
        if self.progress_count == 0:
            return 0
        return self.elapsed_time / self.progress_count

    @property
    def estimated_time_remaining(self) -> float:
        return self.time_per_count * (self.max_count - self.progress_count)


status_icons = {TaskStatus.SUCCESS: icon_filepath('success.png'),
                TaskStatus.ERROR: icon_filepath('error.png'),
                TaskStatus.RUNNING: icon_filepath('running.png'),
                TaskStatus.INITIALIZED: icon_filepath('pending.png'),
                TaskStatus.CANCELLED: icon_filepath('cancelled.png')}


class TaskTab(LayoutSection):
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
        self.task_progress_update_key = task_status_update_key(self.task_key)

        # GUI element keys
        self._text_title_key = f'--tt-text-title-{self.task_key}--'
        self._pb_key = f'--tt-progress-bar-{self.task_key}--'
        self._elapsed_key = f'--tt-elapsed-{self.task_key}--'
        self._counter_key = f'--tt-counter-{self.task_key}--'
        self._iteration_time_key = f'--tt-iteration-time-{self.task_key}--'
        self._status_key = f'--tt-status-{self.task_key}--'
        self._output_files_key = f'--tt-output-files-{self.task_key}--'

        # GUI Button events
        self._cancel_event_key = f'--cancel-{self.task_key}--'

        self.is_cancelled = False

        self.images = {}

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
        output_files = sg.Column([[]], key = self._output_files_key)
        cancel_button = sg.Button('Cancel', key=self._cancel_event_key, disabled=True)
        layout = [[status_icon, title, pb, time_elapsed, counter, avg_iteration_time],
                  [output_files],
                  [cancel_button]]
        return layout

    def handle(self, window, event, values):
        # cancel button clicked
        if event == self._cancel_event_key:
            self.is_cancelled = True
            return

        # if a progress event for any of the tasks comes through
        if event != self.task_progress_update_key:
            return

        progress: ProgressGUIEventData = values[event]
        self._update_avg_iteration_time(window, progress.time_per_count)
        self._update_time_elapsed(window, progress.elapsed_time, progress.estimated_time_remaining)
        self._update_pb(window, progress.progress_count, progress.max_count)
        self._update_counter(window, progress.progress_count, progress.max_count)
        self._update_status(window, progress.task_status)
        self._update_output_files(window, progress.output_files)

    def _update_status(self, window: sg.Window, status: TaskStatus):
        icon_fp = status_icons.get(status, None)
        window[self._status_key].update(filename=icon_fp)

        if status == TaskStatus.RUNNING:
            window[self._cancel_event_key](disabled=False)
        else:
            window[self._cancel_event_key](disabled=True)

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

    def _update_output_files(self, window: sg.Window, output_files: Optional[List[str]]):
        if not output_files or len(output_files) == 0:
            return
        new_elems = []
        for fp in output_files:
            new_elems.append([sg.T(fp)])
        # list_txt = ['%s\n' % fp for fp in output_files]
        # window[self._output_files_key](value=list_txt)
        window.extend_layout(window[self._output_files_key], new_elems)
        pass

    def layout_name(self) -> str:
        return self.task_progress_update_key


class TaskRunnerTab():
    def __init__(self, layout, task_key, visible):
        self._layout = layout
        self.task_key = task_key
        self.tab_button_key = f'-tab-button-{self.task_key}-'
        self.tab_contents_key = f'-tab-contents-{self.task_key}-'
        self.tab_status_key = f'-tab-status-{self.task_key}-'
        self.tab_status_update_key = task_status_update_key(self.task_key)
        self.visible = visible

    def get_layout(self):
        return sg.Column(self._layout, visible=self.visible, key=self.tab_contents_key)

    def update_status(self, window: sg.Window, status: TaskStatus):
        icon_fp = status_icons.get(status, None)
        if icon_fp is None: return
        window[self.tab_status_key].update(filename=icon_fp)

    # def update(self):


class TaskRunnerTabGroup(LayoutSection):
    button_color_off = 'snow'
    button_color_on = 'azure'

    def __init__(self, items):
        tabs = []
        visible = True
        for tab in items:
            tabs.append(TaskRunnerTab(tab[0], tab[1], visible))
            visible = False
        self.tabs = {t.tab_contents_key: t for t in tabs}
        self.tabs_by_task_key = {t.task_key: t for t in tabs}
        self.tab_event_keys = [t.tab_button_key for t in self.tabs.values()]
        self.update_event_keys = {t.tab_status_update_key: t for t in self.tabs.values()}

    def get_layout(self):
        # Calculate sizings
        icon_dim = 24
        max_name = 0
        for t in self.tabs.values():
            if len(t.task_key) > max_name:
                max_name = len(t.task_key)

        row_height = 25
        calculated_height = len(self.tabs.values()) * row_height
        min_height, max_height = 20 * row_height, 30 * row_height
        height = min(max(min_height, calculated_height), max_height)

        calculated_width = max_name * 9
        min_width, max_width = 10 * 9, 100 * 9
        width = min(max(min_width, calculated_width), max_width) + icon_dim

        # Create layout elements
        tabs = []
        contents = []
        selected_name = None
        for t in self.tabs.values():
            color = self.button_color_on if t.visible else self.button_color_off
            if t.visible: selected_name = t.task_key

            tab_col = [sg.Column([[sg.Image(size=(icon_dim, icon_dim),
                                            key=t.tab_status_key,
                                            pad=((0, 0), (0, 0)),
                                            background_color=self.button_color_off),
                                   sg.Button(t.task_key,
                                             key=t.tab_button_key,
                                             pad=((0, 0), (0, 0)),
                                             button_color=color,
                                             mouseover_colors=self.button_color_on,
                                             border_width=0)]], background_color=color, size=(width, row_height),
                                 pad=((0, 0), (0, 0)))]
            tabs.append(tab_col)
            contents.append(t.get_layout())

        scrollable_tabs = sg.Column(tabs, scrollable=True, vertical_scroll_only=True, size=(width, height),
                                    background_color=self.button_color_off)

        layout = [[scrollable_tabs, sg.Frame(f'Task Progress: {selected_name}', [contents], vertical_alignment='top',
                                             key='-progress-frame-')]]
        return layout

    # def select_tab(self, window, task_key):
    #     tab = self.tabs_by_task_key[task_key]
    #     event = tab.tab_button_k
    #     self.handle(window, event, None)
    #
    def handle(self, window, event, values):
        if event in self.tab_event_keys:
            for tab_content_k, tab in self.tabs.items():
                tab_button_k = tab.tab_button_key
                if tab_button_k != event:
                    window.FindElement(tab_content_k).Update(visible=False)
                    window.FindElement(tab_button_k).Update(button_color=self.button_color_off)
                    # window.FindElement(tab.tab_status_key).Update(background_color=self.button_color_off)
            for tab_content_k, tab in self.tabs.items():
                tab_button_k = tab.tab_button_key
                if tab_button_k == event:
                    window.FindElement(tab_content_k).Update(visible=True)
                    window.FindElement(tab_button_k).Update(button_color=self.button_color_on)
                    window.FindElement('-progress-frame-').Update(value=f'Task Progress: {tab.task_key}')
                    # window.FindElement(tab.tab_status_key).Update(background_color=self.button_color_on)

        elif event in self.update_event_keys:
            progress: ProgressGUIEventData = values[event]
            tab = self.update_event_keys[event]
            tab.update_status(window, progress.task_status)

    # self.Widget.yview_moveto(percent_from_top)
    # https://github.com/PySimpleGUI/PySimpleGUI/issues/3320
    # https://github.com/PySimpleGUI/PySimpleGUI/issues/1878

    @property
    def layout_name(self):
        return 'Tabs'
