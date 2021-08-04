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