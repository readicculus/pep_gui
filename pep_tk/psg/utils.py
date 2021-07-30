import PySimpleGUI as sg

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