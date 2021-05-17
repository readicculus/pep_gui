from config import PipelineManifest
from layouts import DatasetSelectionLayout, PipelineSelectionLayout
from datasets import DatasetManifest
from fonts import Fonts
from initial_setup import initial_setup, SettingsNames
from layouts.tabs import LayoutSection
from view import get_settings
import PySimpleGUI as sg
sg.theme('SystemDefaultForReal')
initial_setup()

gui_settings = get_settings()

pm = PipelineManifest()
dm = DatasetManifest(manifest_filepath=gui_settings[SettingsNames.dataset_manifest_filepath])


dataset_tab = DatasetSelectionLayout(dm)
pipeline_tab = PipelineSelectionLayout(pm)

def create_frame(tl: LayoutSection):
    return sg.Frame(layout=tl.get_layout(), title=tl.tab_name, font=Fonts.title_medium, title_color='#0b64c5')



layout = [[sg.Text('Polar Ecosystems Program Batch Runner', size=(38, 1), justification='center', font=Fonts.title_large,
                   relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True, text_color='#063970')]]

layout += [[create_frame(dataset_tab)],
           [create_frame(pipeline_tab)]]

layout += [[sg.Button('Create Run')]]
# layout += [[sg.TabGroup([[
#                             sg.Tab(dataset_tab.tab_name(), dataset_tab.get_layout()),
#                             sg.Tab(pipeline_tab.tab_name(), pipeline_tab.get_layout())
#                         ]], key='-TAB GROUP-', font=Fonts.tab_text)]]
location = (0,0)
if SettingsNames.window_location in gui_settings.get_dict():
    location = gui_settings[SettingsNames.window_location]
window = sg.Window('GUI', layout,
                   default_element_size=(12, 1), location=location)

while True:
    event, values = window.read()
    # sg.popup_non_blocking(event, values)
    print(event, values)
    try:
        gui_settings[SettingsNames.window_location] = window.CurrentLocation()
    except: pass
    if event == sg.WIN_CLOSED:           # always,  always give a way out!
        break
    dataset_tab.handle(window, event, values)
    pipeline_tab.handle(window, event, values)
window.close()