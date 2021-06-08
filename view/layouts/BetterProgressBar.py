import PySimpleGUI as sg
from dataclasses import dataclass
from typing_extensions import TypedDict

from core.job import TaskStatus
from layouts.layout import LayoutSection

@dataclass
class ProgressGUIEventData:
    type: str  # type of event?
    progress_count: int       # number of items processed already in task
    max_count: int            # number of items being processed in task
    elapsed_time: float       # time elapsed so far
    task_status: TaskStatus   # current status of the task



class BetterProgressBar(LayoutSection):
    def __init__(self, task_key):
        self.task_key = task_key

    def get_layout(self):
        title = sg.T(self.task_key,  size=(len(self.task_key), 1), key=self.text_title_key)
        pb = sg.ProgressBar(100, orientation='hs', size=(20,4), key=self.pb_key)
        time_elapsed_remaining = sg.T('', key=self.elapsed_key, size=(8,1))  # size of time 00:00:00
        counter = sg.T('00000/00000', key=self.counter_key, size=(len('00000/00000'),1))
        return [title, pb, time_elapsed_remaining, counter]

    def handle(self, window, event, values):
        if event != self.update_event_key:
            return

        progress : ProgressGUIEventData = values[event]
        window[self.pb_key].update_bar(progress.type, 100)

    def event_keys(self):
        return [self.pb_key, self.elapsed_key, self.counter_key]

    @property
    def update_event_key(self):
        return f'--update-{self.task_key}--'

    @property
    def text_title_key(self):
        return f'--text-title-{self.task_key}--'

    @property
    def pb_key(self):
        return f'--progress-bar-{self.task_key}--'

    @property
    def elapsed_key(self):
        return f'--elapsed-{self.task_key}--'

    @property
    def counter_key(self):
        return f'--counter-{self.task_key}--'

    @property
    def layout_name(self) -> str:
        return self.task_key
