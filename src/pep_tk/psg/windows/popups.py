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

from typing import Tuple, Optional
import PySimpleGUI as sg

from pep_tk.psg.fonts import Fonts
from pep_tk.psg.settings import image_resource_path


def popup_error(msg: str, parent_window_loc: Optional[Tuple[int,int]] = None, parent_window_size: Optional[Tuple[int,int]] = None):
    if parent_window_loc is None or parent_window_size is None:
        sg.popup_ok(msg, title='Uh oh', keep_on_top=True)
    else:
        max_line_width = 200
        current = sg.MESSAGE_BOX_LINE_WIDTH
        for line in msg.split('\n'):
            if len(line) > current:
                current = len(line)

        (win_x, win_y) = parent_window_loc
        (win_w, win_h) = parent_window_size
        dim_multiplier = 7
        popup_w = dim_multiplier * min(max_line_width, current)
        popup_h = 50 + dim_multiplier * len(msg.split('\n'))
        cx = int(win_w / 2 - popup_w / 2)
        cy = int(win_h / 2 - popup_h / 2)
        sg.popup_ok(msg, title='Uh oh', line_width=popup_w, location=(win_x + cx, win_y + cy), keep_on_top=True)

def popup_about(location=(None,None)):
    from pep_tk import __version__
    message = f'PEP GUI Version {__version__}\n' \
              f'Developed by Yuval Boss\n' \
              f'https://github.com/readicculus/pep_gui'

    # sg.popup_no_buttons(message, title='About', line_width=200, location=location, modal=True, keep_on_top=True,
    #                      font=Fonts.tab_text)
    w=max([len(x) for x in message.split('\n')])
    l = [[sg.Column([[sg.Image(filename=image_resource_path('icon_160x160.png'))]], vertical_alignment='center', justification='center',  k='-C-')],
         [sg.Multiline(default_text=message, disabled=True, no_scrollbar=True, expand_y=True, size=(w,3))]]
    window = sg.Window(layout=l, title='About', modal=True, keep_on_top=True, location=location, font=Fonts.tab_text, finalize=True)
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            window.close()
            break
