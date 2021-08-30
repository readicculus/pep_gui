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

import PySimpleGUI as sg
from PySimpleGUI import COLOR_SYSTEM_DEFAULT
def move_window_onto_screen(window: sg.Window):
    # move back on screen if off screen for some reason
    s_w, s_h = window.get_screen_size()
    win_w, win_h = window.size
    loc_x, loc_y = window.current_location()
    if loc_x + win_w >= s_w:
        loc_x = s_w - win_w - 20
    elif loc_x < 0:
        loc_x = 0
    if loc_y + win_h >= s_h:
        loc_y = s_h - win_h - 20
    elif loc_y < 0:
        loc_y = 0
    window.move(loc_x, loc_y)

def set_pep_theme(sg_lib):
    name, theme = "PEP_THEME", {"BACKGROUND": "#FAFAFA", "TEXT": COLOR_SYSTEM_DEFAULT, "INPUT": COLOR_SYSTEM_DEFAULT,
                             "TEXT_INPUT": COLOR_SYSTEM_DEFAULT, "SCROLL": COLOR_SYSTEM_DEFAULT, "BUTTON": COLOR_SYSTEM_DEFAULT,
                             "PROGRESS": COLOR_SYSTEM_DEFAULT, "BORDER": 1, "SLIDER_DEPTH": 1, "PROGRESS_DEPTH": 0, }
    sg_lib.theme_add_new(name, theme)
    sg_lib.theme(name)