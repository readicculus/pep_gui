import datetime
from typing import List, Optional, Dict

import PySimpleGUI as sg
from dataclasses import dataclass

from pep_tk.core.job import TaskStatus
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import LayoutSection
from pep_tk.psg.settings import icon_filepath
from pep_tk.psg.utils import set_pep_theme

set_pep_theme(sg)

@dataclass
class ProgressGUIEventData:
    """ Data message communicated between the Scheduler thread and the main GUI thread """
    progress_count: int = None  # number of items processed already in task
    max_count: int = None  # number of items being processed in task
    elapsed_time: float = None  # time elapsed so far
    task_status: TaskStatus = None  # current status of the task
    output_files: List[str] = None  # output files from the task (image lists, detections)
    output_log: str = None

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

def task_status_update_key(task_key):
    return f'--task-update-{task_key}--'


# Status icons to display in the tabs for each task
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
    MAX_STDOUT_LINES = None

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
        self._kwiver_output_key = f'--tt-kwiver-output-{self.task_key}--' + sg.WRITE_ONLY_KEY

        # GUI Button events
        self._cancel_event_key = f'--cancel-{self.task_key}--'

        self.is_cancelled = False

        self.images = {}

    def get_layout(self):
        def empty_string(s):
            return ' ' * len(s)

        status_icon = sg.Image(size=(24, 24), key=self._status_key)
        title = sg.T(self.task_key, size=(len(self.task_key), 1), key=self._text_title_key, font=Fonts.title_medium)
        pb = sg.ProgressBar(100, orientation='hs', size=(20, 4), key=self._pb_key)
        elapsed_str = empty_string('00:00:00 elapsed 00:00:00 remaining')
        time_elapsed = sg.T(elapsed_str, key=self._elapsed_key)
        counter_str = empty_string('00000/00000')
        counter = sg.T(counter_str, key=self._counter_key)
        iter_str = empty_string('x.xx seconds/iter')
        avg_iteration_time = sg.T(iter_str, key=self._iteration_time_key, size=(len('x.xx seconds/iter'), 1))
        output_files = sg.Column([[]], key=self._output_files_key)
        cancel_button = sg.Button('Cancel', key=self._cancel_event_key, disabled=True)
        output_title = sg.T("Output Log", font=Fonts.title_small)
        kwiver_output = sg.Multiline( key=self._kwiver_output_key,
                                      autoscroll=False, auto_refresh=True, disabled=True, expand_x=True, expand_y=True, size=(50,10))
        layout = [[status_icon, title, pb, time_elapsed, counter, avg_iteration_time],
                  [output_files],
                  [cancel_button],
                  [output_title],
                  [kwiver_output]]
        return layout

    def handle(self, window, event, values):
        # cancel button clicked
        if event == self._cancel_event_key or self.is_cancelled:
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
        self._update_kwiver_output(window, progress.output_log)

    def _update_status(self, window: sg.Window, status: TaskStatus):
        if status is None:
            return
        icon_fp = status_icons.get(status, None)
        window[self._status_key].update(filename=icon_fp)

        if status == TaskStatus.RUNNING:
            window[self._cancel_event_key](disabled=False)
        else:
            window[self._cancel_event_key](disabled=True)

    def _update_kwiver_output(self, window: sg.Window, new_str: str):
        if new_str is None or new_str == "":
            return
        window[self._kwiver_output_key].print(new_str.strip(), autoscroll=True)

        # if self.MAX_STDOUT_LINES is not None:
        #     lines = window[self._kwiver_output_key].get().split('\n')
        #     line_ct = len(lines)
        #     if line_ct > self.MAX_STDOUT_LINES:
        #         end_lines = lines[-self.MAX_STDOUT_LINES:]
        #         end_lines += new_str.split('\n')
        #         window[self._kwiver_output_key].update(value='\n'.join(end_lines), append=False)
        #         return
        #
        # lines = new_str.split('\n')
        # for line in lines:
        #     text_color = None
        #     if 'INFO' in line:
        #         text_color = 'blue'
        #     elif 'WARNING' in line:
        #         text_color = 'orange'
        #     elif 'ERROR' in line:
        #         text_color = 'red'
        #     window[self._kwiver_output_key].print(line, end='\n', autoscroll=False, text_color=text_color)

    def _update_avg_iteration_time(self, window: sg.Window, avg_iteration_time: float):
        if avg_iteration_time is None:
            return
        fmt = '%.2f seconds/iter' % avg_iteration_time
        window[self._iteration_time_key](value=fmt)

    def _update_time_elapsed(self, window: sg.Window, elapsed_time: float, remaining_time: float):
        if elapsed_time is None or remaining_time is None:
            return
        elapsed = str(datetime.timedelta(seconds=int(elapsed_time)))
        remaining = str(datetime.timedelta(seconds=int(remaining_time)))
        v = '%s elapsed %s remaining' % (elapsed, remaining)
        window[self._elapsed_key](value=v)

    def _update_pb(self, window: sg.Window, count: int, max_count: int):
        if count is None or max_count is None: return
        window[self._pb_key].update_bar(count, max_count)

    def _update_counter(self, window: sg.Window, count: int, max_count: int):
        if count is None or max_count is None: return
        window[self._counter_key](value='%d/%d' % (count, max_count))

    def _update_output_files(self, window: sg.Window, output_files: Optional[List[str]]):
        if not output_files or len(output_files) == 0:
            return
        new_elems = [[sg.T('Output Files:', font=Fonts.title_small)]]
        w = max([len(x) for x in output_files])
        new_elems.append([sg.Multiline('\n'.join(output_files), disabled=True, size=(w,len(output_files)))])
        window.extend_layout(window[self._output_files_key], new_elems)

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
        return sg.Column(self._layout, visible=self.visible, key=self.tab_contents_key, expand_y=True)

    def update_status(self, window: sg.Window, status: TaskStatus):
        icon_fp = status_icons.get(status, None)
        if icon_fp is None: return
        window[self.tab_status_key].update(filename=icon_fp)


class TaskRunnerTabGroup(LayoutSection):
    button_color_off = ('black', sg.LOOK_AND_FEEL_TABLE[sg.CURRENT_LOOK_AND_FEEL]["BACKGROUND"])
    button_color_on = ('black', 'azure')

    def __init__(self, items):
        tabs = []
        self.current_tab = None
        for tab in items:
            t = TaskRunnerTab(tab[0], tab[1], visible=self.current_tab is None)
            tabs.append(t)
            if self.current_tab is None:
                self.current_tab = t
        self.tabs_by_task_key : Dict[str, TaskRunnerTab] = {t.task_key: t for t in tabs}
        self.tab_button_event_keys : Dict[str, TaskRunnerTab] = {t.tab_button_key: t for t in tabs}
        self.tab_contents_event_keys : Dict[str, TaskRunnerTab] = {t.tab_contents_key: t for t in tabs}
        self.update_event_keys : Dict[str, TaskRunnerTab] = {t.tab_status_update_key: t for t in tabs}
        self._tasks_started_flags = []

    def get_layout(self):
        # Calculate sizings
        icon_dim = 24
        max_name = 0
        max_allowable_name_len = 100
        for t in self.tabs_by_task_key.values():
            if len(t.task_key) > max_name:
                max_name = len(t.task_key)
        max_name = min(max_name, max_allowable_name_len)

        row_height = 30
        calculated_height = len(self.tabs_by_task_key.values()) * row_height
        min_height, max_height = 20 * row_height, 30 * row_height
        height = min(max(min_height, calculated_height), max_height)

        calculated_width = int(max_name * 8.5)
        min_width, max_width = 10 * 9, max_allowable_name_len * 9
        btn_width = min(max(min_width, calculated_width), max_width)
        col_width = btn_width + icon_dim
        # Create layout elements
        tabs = []
        contents = []
        selected_name = ""
        def make_max_name_len(name):
            cur_len = len(name)
            spaces = " "* ((max_name - cur_len))
            return name + spaces

        for t in self.tabs_by_task_key.values():
            tab_col = \
                [sg.Image(size=(icon_dim, icon_dim),
                                            key=t.tab_status_key,
                                            pad=((0, 0), (0, 0)),
                                            background_color=self.button_color_off[1]),
                                   sg.Button(make_max_name_len(t.task_key),
                                             key=t.tab_button_key,
                                             pad=((0, 0), (0, 0)),
                                             button_color=self.button_color_off,
                                             use_ttk_buttons=True,
                                             mouseover_colors=self.button_color_on,
                                             border_width=0)]
            tabs.append(tab_col)
            contents.append(t.get_layout())

        scrollable_tabs = sg.Column(tabs, scrollable=True, vertical_scroll_only=True, size=(col_width, height),
                                    background_color=self.button_color_off[1], pad=((0, 0), (0, 0)), vertical_alignment='top')

        tab_contents = sg.Frame(f'Task Progress: {selected_name}', [contents], vertical_alignment='top',
                 key='-progress-frame-')
        layout = [[scrollable_tabs, tab_contents]]
        return layout

    def select_tab(self, window, event_tab_btn_key = None):
        if event_tab_btn_key == self.current_tab.tab_button_key:
            return
        if event_tab_btn_key is None:
            event_tab_btn_key = self.current_tab.tab_button_key
        # Hide other current tab
        window[self.current_tab.tab_contents_key].Update(visible=False)
        window[self.current_tab.tab_button_key].Update(button_color=self.button_color_off)
        window[self.current_tab.tab_button_key].set_focus(False)
        # Make new tab visible
        tab = self.tab_button_event_keys[event_tab_btn_key]
        window[tab.tab_contents_key].Update(visible=True)
        window[tab.tab_button_key].Update(button_color=self.button_color_on)
        window[tab.tab_button_key].set_focus(True)
        window[tab.tab_contents_key].expand(True,True,True)
        window['-progress-frame-'].Update(value=f'Task Progress: {tab.task_key}')
        self.current_tab = tab

    def handle(self, window, event, values):
        if event in self.tab_button_event_keys:
            self.select_tab(window, event)

        elif event in self.update_event_keys:
            progress: ProgressGUIEventData = values[event]
            self.update_event_keys[event].update_status(window, progress.task_status)
            task_key = self.update_event_keys[event].task_key
            if progress.task_status == TaskStatus.RUNNING and task_key not in self._tasks_started_flags:
                self._tasks_started_flags.append(task_key)
                self.select_tab(window, self.update_event_keys[event].tab_button_key)

    @property
    def layout_name(self):
        return 'Tabs'
