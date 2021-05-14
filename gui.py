from config import PipelineManifest
from dataset_selection import DatasetSelectionLayout
from datasets import DatasetManifest
from fonts import Fonts
from initial_setup import initial_setup, SettingsNames
from pipeline_selection import PipelineSelectionLayout
from view import get_settings
import PySimpleGUI as sg
initial_setup()

gui_settings = get_settings()

pm = PipelineManifest()
dm = DatasetManifest(manifest_filepath=gui_settings[SettingsNames.dataset_manifest_filepath])


dataset_tab = DatasetSelectionLayout(dm.list_dataset_keys())
pipeline_tab = PipelineSelectionLayout(pm)


layout = [[sg.Text('Polar Ecosystems Program Batch Runner', size=(38, 1), justification='center', font=Fonts.title_large,
                   relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True)]]
layout += [[sg.TabGroup([[
                            sg.Tab(dataset_tab.tab_name(), dataset_tab.get_layout()),
                            sg.Tab(pipeline_tab.tab_name(), pipeline_tab.get_layout())
                        ]], key='-TAB GROUP-', font=Fonts.tab_text)]]


window = sg.Window('GUI', layout,
                   default_element_size=(12, 1))

while True:
    event, values = window.read()
    # sg.popup_non_blocking(event, values)
    print(event, values)
    if event == sg.WIN_CLOSED:           # always,  always give a way out!
        break
    dataset_tab.handle(window, event, values)
    pipeline_tab.handle(window, event, values)
window.close()