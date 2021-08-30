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

from typing import List

import PySimpleGUI as sg

from pep_tk.core.parser import ManifestParser
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import LayoutSection, help_icon

class DatasetSelectionLayout(LayoutSection):
    def __init__(self, dataset_manifest: ManifestParser, event_key='_dataset_tab_', selected_datasets=None):
        self.dataset_manifest: ManifestParser = dataset_manifest
        self.datasets: List[str] = self.dataset_manifest.list_dataset_keys()
        self.selected_datasets = selected_datasets or []
        self.event_key = event_key
        self.right_button_key = '%s>' % self.event_key
        self.left_button_key = '%s<' % self.event_key
        self.selected_datasets_title_key = '%s_selected_datasets_title'

    def get_selected_datasets(self):
        return [self.dataset_manifest[ds_name] for ds_name in self.selected_datasets]

    def get_layout(self):
        dataset_column_size = (40, max(10 , min(15, len(self.datasets)))) # show at minimum 10 rows and at most 25 rows.
        layout = [[sg.T('Select a dataset or multiple datasets below.\n'
                        'Select multiple by clicking on multiple datasets then pressing the \'>\' button', font=Fonts.description),
                        help_icon('Use ctrl+click to select multiple, shift-click to select many.')],
                  [
                      sg.Column([
                          [sg.Text('Datasets', font=Fonts.tab_text)],
                                 [sg.Listbox(key='dataset_options',
                                             values=self.datasets,
                                             size=dataset_column_size,
                                             select_mode=sg.SELECT_MODE_EXTENDED,
                                             bind_return_key=True,
                                             font=Fonts.description,
                                             background_color='white')]
                      ]),
                      sg.Column([[sg.Text('\n')], [sg.Button('>', key=self.right_button_key)], [sg.Button('<', key=self.left_button_key)]]),
                      sg.Column([
                          [sg.Text('Selected Datasets %d' % len(self.selected_datasets),
                                   key=self.selected_datasets_title_key,
                                   size=(len('selected datasets x') + 5, 1),
                                   font=Fonts.tab_text)],
                          [sg.Listbox(key='selected_datasets',
                                      values=self.selected_datasets,
                                      size=dataset_column_size,
                                      select_mode=sg.SELECT_MODE_EXTENDED,
                                      bind_return_key=True,
                                      font=Fonts.description,
                                      background_color='white')]
                      ])
                  ],
                  [sg.Text('Filter:', font=Fonts.tab_text),
                   sg.InputText(key='datasets_filter', enable_events=True, size=(30, 1), background_color='white'),
                   sg.Button('clear filter', key='clear_filter', font=Fonts.tab_text)],
                  [sg.Text('', key='warning', text_color='red', size=(50, 1), font=Fonts.tab_text)]]
        return layout

    def handle(self, window, event, values):
        need_update = False
        if event == 'datasets_filter':
            exp = values['datasets_filter']
            if exp == '':
                self.datasets = self.dataset_manifest.list_dataset_keys()
            else:
                self.datasets = self.dataset_manifest.list_dataset_keys_txt(values['datasets_filter'] + '*')
            need_update = True
        elif event == 'clear_filter':
            window['datasets_filter'](value='')
            window.write_event_value('datasets_filter', '')
        elif event == self.right_button_key:
            selection = values['dataset_options']
            for s in selection:
                self.selected_datasets.append(s)

            need_update = True

        elif event == self.left_button_key:
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
            window['dataset_options'].Update(values=unselected_values)
            window['selected_datasets'].Update(values=datasets_selected)
            window[self.selected_datasets_title_key].Update(
                value='Selected Datasets (%d)' % len(self.selected_datasets))

    @property
    def layout_name(self):
        return 'Dataset Selection'
