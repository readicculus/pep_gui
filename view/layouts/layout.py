import abc
import PySimpleGUI as sg

from settings import resources_directory


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


# SYMBOL_UP = '▲'
# SYMBOL_DOWN = '▼'
#
#
# def collapse(layout, key):
#     """
#     Helper function that creates a Column that can be later made hidden, thus appearing "collapsed"
#     :param layout: The layout for the section
#     :param key: Key used to make this seciton visible / invisible
#     :return: A pinned column that can be placed directly into your layout
#     :rtype: sg.pin
#     """
#     return sg.pin(sg.Column(layout, key=key))

def Collapsible(layout, key, title='', arrows=(sg.SYMBOL_DOWN, sg.SYMBOL_UP), collapsed=False):
    """
    User Defined Element
    A "collapsable section" element. Like a container element that can be collapsed and brought back
    :param layout:Tuple[List[sg.Element]]: The layout for the section
    :param key:Any: Key used to make this section visible / invisible
    :param title:str: Title to show next to arrow
    :param arrows:Tuple[str, str]: The strings to use to show the section is (Open, Closed).
    :param collapsed:bool: If True, then the section begins in a collapsed state
    :return:sg.Column: Column including the arrows, title and the layout that is pinned
    """
    return sg.Column([[sg.T((arrows[1] if collapsed else arrows[0]), enable_events=True, k=key+'-BUTTON-'),
                       sg.T(title, enable_events=True, key=key+'-TITLE-')],
                      [sg.pin(sg.Column(layout, key=key, visible=not collapsed, metadata=arrows))]], pad=(0,0))

def help_icon(tooltip, key=None):
    if key is None:
        key = hash(tooltip)
    return sg.Image(resources_directory('help.png'), tooltip=tooltip, key=key, size=(16,16))