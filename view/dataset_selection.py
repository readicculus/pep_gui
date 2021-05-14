import PySimpleGUI as sg

from fonts import Fonts
from tabs import TabLayout


class DatasetSelectionLayout(TabLayout):
    def __init__(self, datasets, event_key= '_dataset_tab_', selected_datasets = None):
        self.datasets = datasets
        self.selected_datasets = selected_datasets or []
        self.event_key = event_key
        self.right_button_key = '%s>'% self.event_key
        self.left_button_key = '%s<'% self.event_key
        self.selected_datasets_title_key = '%s_selected_datasets_title'

    def get_layout(self):
        size = (40, max(min(40, len(self.datasets)), 20))
        layout = [[sg.Column([[sg.Text('Datasets')],
                               [sg.Listbox(key='dataset_options',
                                           values=self.datasets,
                                           size=size, select_mode='multiple', bind_return_key=True,font=Fonts.description)]]),
                    sg.Column([[sg.Text('\n')], [sg.Button('>', key=self.right_button_key)], [sg.Button('<', key=self.left_button_key)]]),
                    sg.Column([[sg.Text('Selected Datasets %d' % len(self.selected_datasets), key=self.selected_datasets_title_key)],
                               [sg.Listbox(key='selected_datasets',
                                           values=self.selected_datasets,
                                           size=size,
                                           select_mode='multiple',
                                           bind_return_key=True,
                                           font=Fonts.description)]])],
                   [sg.Text('', key='warning', text_color='red', size=(50, 1))],
                   [sg.CButton('Submit')]]
        return layout

    def handle(self, window, event, values):
        need_update = False
        if event == self.right_button_key:
            selection = values['dataset_options']
            for s in selection:
                self.selected_datasets.append(s)

            need_update = True

        if event == self.left_button_key:
            selected_datasets = values['selected_datasets']
            for s in selected_datasets:
                self.selected_datasets.remove(s)
            need_update = True

        if need_update:
            unselected_values = []
            for v in self.datasets:
                if not v in self.selected_datasets:
                    unselected_values.append(v)
            unselected_values = sorted(unselected_values)
            datasets_selected = sorted(self.selected_datasets)
            window.FindElement('dataset_options').Update(values=unselected_values)
            window.FindElement('selected_datasets').Update(values=datasets_selected)
            window.FindElement(self.selected_datasets_title_key).Update(value='Selected Datasets (%d)' % len(self.selected_datasets))

    def tab_name(self):
        return 'Dataset Selection'


