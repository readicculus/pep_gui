import abc

class LayoutSection(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_layout(self):
        return

    @abc.abstractmethod
    def handle(self, window, event, values):
        return

    @property
    @abc.abstractmethod
    def layout_name(self) -> str:
        return ''