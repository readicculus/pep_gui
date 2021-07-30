import PySimpleGUI as sg

def make_window(title, layout, **kwargs) -> sg.Window:
    menu_def = [['&File', ['&Resume Job     Ctrl-R::-resume-menu-btn-', '&Properties::-properties-menu-btn-',
                           'E&xit::-exit-menu-btn-']],
                ['&Help', '&About...::-about-menu-btn-'], ]

    menu = [[sg.Menu(menu_def, tearoff=False, pad=(200, 1))]]
    layout = menu + layout

    window = sg.Window(title,layout, **kwargs)
    window.extend_layout
    return window

