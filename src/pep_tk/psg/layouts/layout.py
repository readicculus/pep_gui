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

import abc
import PySimpleGUI as sg

from pep_tk.psg.settings import image_resource_path


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


def Menubar(menu_def, text_color, background_color, pad=(0, 0)):
    """
    A User Defined element that simulates a Menu element by using ButtonMenu elements
    :param menu_def: A standard PySimpleGUI menu definition
    :type menu_def: List[List[Tuple[str, List[str]]]
    :param text_color: color for the menubar's text
    :type text_color:
    :param background_color: color for the menubar's background
    :type background_color:
    :param pad: Amount of padding around each menu entry
    :type pad:
    :return: A column element that has a row of ButtonMenu buttons
    :rtype: sg.Column
    """
    row = []
    for menu in menu_def:
        text = menu[0]
        if sg.MENU_SHORTCUT_CHARACTER in text:
            text = text.replace(sg.MENU_SHORTCUT_CHARACTER, '')
        if text.startswith(sg.MENU_DISABLED_CHARACTER):
            disabled = True
            text = text[len(sg.MENU_DISABLED_CHARACTER):]
        else:
            disabled = False
        row += [sg.ButtonMenu(text, menu, border_width=0, button_color=f'{text_color} on {background_color}',key=text, pad=pad, disabled=disabled)]

    return sg.Column([row], background_color=background_color, pad=(0,0), expand_x=True)

def help_icon(tooltip, key=None):
    if key is None:
        key = str(hash(tooltip))
    return sg.Image(image_resource_path('help.png'), tooltip=tooltip, key=key, size=(16, 16))