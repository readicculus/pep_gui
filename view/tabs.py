import PySimpleGUI as sg
import abc

class TabLayout(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_layout(self):
        return

    @abc.abstractmethod
    def handle(self, window, event, values):
        return

    @property
    @abc.abstractmethod
    def tab_name(self) -> str:
        return ''