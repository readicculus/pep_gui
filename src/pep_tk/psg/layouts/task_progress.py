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
from typing import List, Optional, Dict

import PySimpleGUI as sg

from pep_tk.core.job import TaskStatus
from pep_tk.psg.events import ProgressGUIEventData
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import LayoutSection
from pep_tk.psg.settings import icon_filepath
from pep_tk.psg.utils import set_pep_theme

set_pep_theme(sg)

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


        self.images = {}
        self.max_count = 0
        self.progress_count = 0
        self.is_cancelled = False
        self.status = None
        self.completed_on_load = None

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
        if not self.completed_on_load:
            self.completed_on_load = progress.completed_on_load
        self._update_avg_iteration_time(window, progress.time_per_count)
        self._update_time_elapsed(window, progress.elapsed_time, progress.estimated_time_remaining)
        self._update_pb(window, progress.progress_count, progress.max_count)
        self._update_counter(window, progress.progress_count, progress.max_count)
        self._update_status(window, progress.task_status)
        self._update_output_files(window, progress.output_files)
        self._update_kwiver_output(window, progress.output_log)

        self.max_count = progress.max_count
        self.progress_count = progress.progress_count

    def _update_status(self, window: sg.Window, status: TaskStatus):
        if status is None:
            return
        self.status = status
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
        self.tab_status_image_key = f'-tab-status-image-{self.task_key}-'
        self.tab_status_update_key = task_status_update_key(self.task_key)
        self.tab_key = f'--tab--{self.task_key}--'
        self.visible = visible

    def get_layout(self):
        return sg.Column(self._layout, visible=self.visible, key=self.tab_contents_key, expand_y=True)

    def update_status(self, window: sg.Window, status: TaskStatus):
        icon_fp = status_icons.get(status, None)
        if icon_fp is None: return
        window[self.tab_status_image_key].Update(filename=icon_fp)


class TaskRunnerTabGroup(LayoutSection):
    button_color_off = ('black', '#eff1f3') # (Text Color, Button Color)
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
                [sg.Frame('', layout=[[sg.Image(size=(icon_dim, icon_dim),
                                                key=t.tab_status_image_key,
                                                pad=((5, 5), (5, 5)),
                                                background_color=self.button_color_off[1]),
                                   sg.Button(make_max_name_len(t.task_key),
                                             key=t.tab_button_key,
                                             pad=((0, 0), (0, 0)),
                                             button_color=self.button_color_off,
                                             use_ttk_buttons=True,
                                             mouseover_colors=self.button_color_on,
                                             border_width=0)]], key = t.tab_key, background_color=self.button_color_off[1])]
            tabs.append(tab_col)
            contents.append(t.get_layout())

        needs_scroll = len(tabs) * row_height > height
        scrollable_tabs =sg.Column(tabs, scrollable=needs_scroll, vertical_scroll_only=True, size=(col_width, height),
                          background_color=self.button_color_off[1], pad=((5, 5), (5, 5)), vertical_alignment='top')


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
        window[self.current_tab.tab_key].Widget.config(background=self.button_color_off[1])
        window[self.current_tab.tab_button_key].Update(button_color=self.button_color_off)

        window[self.current_tab.tab_button_key].ParentRowFrame.config(background=self.button_color_off[1])
        window[self.current_tab.tab_button_key].ParentRowFrame.config(highlightbackground=self.button_color_off[1])
        window[self.current_tab.tab_button_key].ParentRowFrame.config(highlightcolor=self.button_color_off[1])#self.button_color_on[1])
        window[self.current_tab.tab_button_key].set_focus(False)

        # Make new tab visible
        tab = self.tab_button_event_keys[event_tab_btn_key]

        window[tab.tab_contents_key].Update(visible=True)
        window[tab.tab_button_key].Update(button_color=self.button_color_on)
        window[tab.tab_button_key].set_focus(True)
        window[tab.tab_contents_key].expand(True,True,True)

        window[tab.tab_button_key].ParentRowFrame.config(background=self.button_color_on[1])
        window[tab.tab_button_key].ParentRowFrame.config(highlightbackground=self.button_color_on[1])
        window[tab.tab_button_key].ParentRowFrame.config(highlightcolor=self.button_color_on[1])#self.button_color_on[1])

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
