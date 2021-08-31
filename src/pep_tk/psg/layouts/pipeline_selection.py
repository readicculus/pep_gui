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

from typing import Dict, Optional

from pep_tk.core.configuration import PipelineManifest, ConfigOption, PipelineConfig
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import LayoutSection
import PySimpleGUI as sg


def pipeline_key(pipeline_name):
    return f'-F-{pipeline_name}-'


class PipelineConfigLayout(LayoutSection):
    def __init__(self, pipeline_name, pipeline_manifest):
        self.pipeline_name = pipeline_name
        self.pipeline_manifest: PipelineManifest = pipeline_manifest
        self.selected_pipeline: PipelineConfig = self.pipeline_manifest[self.pipeline_name]
        self.event_keys = [self.reset_defaults_key, self.pipeline_frame_key]
        self.input_keys_to_config_name: Dict[str, str] = {}
        # self.current_errors = {}

    def get_layout(self):
        config_layout = []
        config_layout.append([sg.T(self.pipeline_name, font=Fonts.title_medium)])
        config_layout.append([sg.HorizontalSeparator(color='black')])
        opts = self.selected_pipeline.parameters_group.options
        for o in opts:
            k = self.pipeline_config_input_key(o.name)
            self.event_keys.append(k)
            self.input_keys_to_config_name[k] = o.name
            row = [
                sg.T(f'{o.name}:', font=Fonts.description_bold),
                sg.I(key=k, default_text=o.value(), enable_events=True, background_color='white'),
                sg.T(f'({o.validator.description()})', key=self.pipeline_config_warning_key(o.name), text_color='red',
                     visible=False)
            ]
            config_layout.append(row)
            config_layout.append(
                [
                    sg.T(o.description, font=Fonts.description, pad=((0, 0), (0, 0)))
                 ]
            )
            config_layout.append([sg.HorizontalSeparator(color='white')])
        config_layout.append([sg.Button('Reset Defaults', key=self.reset_defaults_key)])
        return config_layout

    def validate(self, values) -> bool:
        for key, opt_name in self.input_keys_to_config_name.items():
            opt = self.selected_pipeline.parameters_group.get_config_option(opt_name)
            ui_value = values[key]
            ok, res = opt.validator.validate(ui_value)
            if not ok:
                return False
        return True

    def handle(self, window, event, values):
        if event == self.reset_defaults_key:
            self.selected_pipeline.parameters_group.reset_all()
            for key, opt_name in self.input_keys_to_config_name.items():
                warning_key = self.pipeline_config_warning_key(opt_name)
                opt = self.selected_pipeline.parameters_group.get_config_option(opt_name)
                window[key].Update(value=opt.value())
                window[key].Update(background_color='White')
                window[warning_key].Update(visible=False)

        elif event in list(self.input_keys_to_config_name.keys()):
            for key, opt_name in self.input_keys_to_config_name.items():
                warning_key = self.pipeline_config_warning_key(opt_name)
                opt = self.selected_pipeline.parameters_group.get_config_option(opt_name)
                config_opt_value = opt.value()
                ui_value = values[key]
                if not str(config_opt_value) == ui_value or key == event:
                    ok, res = opt.validator.validate(ui_value)
                    if ok:
                        opt.set_value(ui_value)
                        window[key].Update(background_color='White')
                        window[warning_key].Update(visible=False)
                    else:
                        window[key].Update(background_color='Red')
                        window[warning_key].Update(visible=True)

    def layout_name(self) -> str:
        return self.pipeline_name

    def pipeline_frame_key(self):
        return pipeline_key(self.pipeline_name)

    def pipeline_config_input_key(self, config_name):
        return f'-IN-{self.pipeline_name}-{config_name}-'

    def pipeline_config_warning_key(self, config_name):
        return f'-WARN-{self.pipeline_name}-{config_name}-'

    @property
    def reset_defaults_key(self):
        return f'-IN-{self.pipeline_name}-reset-'

    def get_opt_from_key(self, k) -> ConfigOption:
        pass


class PipelineSelectionLayout(LayoutSection):
    def __init__(self, pipeline_manifest: PipelineManifest, event_key='_pipeline_tab_'):
        self.pipeline_manifest = pipeline_manifest
        self.selected_pipeline: Optional[PipelineConfig] = None

        # gui element identifier keys
        self.event_key = event_key
        self.combobox_key = '%s_combobox' % self.event_key
        self.reset_defaults_key = '%s_reset_defaults_button' % self.event_key

        # create pipeline config layouts
        self.config_frames = {}
        for p in self.pipeline_manifest.list_pipeline_names():
            layout = PipelineConfigLayout(p, self.pipeline_manifest)
            self.config_frames[layout.pipeline_frame_key()] = layout

    def validate(self, values) -> bool:
        if self.selected_pipeline is None:
            return False
        selected_pipeline_key = pipeline_key(self.selected_pipeline.name)
        return self.config_frames[selected_pipeline_key].validate(values)

    def get_layout(self):
        pipelines = self.pipeline_manifest.list_pipeline_names()
        width = len(max(pipelines, key=len)) + 5
        frames = []
        for frame_key, pipeline_layout in self.config_frames.items():
            l = pipeline_layout.get_layout()
            n = pipeline_layout.pipeline_name
            config_count = len(pipeline_layout.input_keys_to_config_name)
            if config_count <= 3:
                frames.append(sg.Column(
                    [[sg.Frame('', l, font=Fonts.title_small)]],
                    expand_x=True, key=frame_key,
                    visible=False))
            else:
                # put in a scrollable column if  more than 3 configs
                col = [[sg.Column(l, expand_x=True, scrollable=True, vertical_scroll_only=True)]]
                frames.append(sg.Frame('', col, key=frame_key, visible=False, font=Fonts.title_small))
        default_value = '<select a pipeline>'
        return [
            [sg.Text('Select and Configure a pipeline.', font=Fonts.description)],
            [sg.Combo(values=[default_value] + pipelines,
                      size=(width, min(10, len(pipelines) + 1)),
                      default_value=default_value,
                      key=self.combobox_key,
                      font=Fonts.description,readonly=True,
                      enable_events=True)
             ],
            frames
        ]

    def get_selected_pipeline(self):
        return self.selected_pipeline

    # event loop handler
    def handle(self, window, event, values):
        if event == self.combobox_key:
            selected_pipeline_name = values[self.combobox_key]
            if selected_pipeline_name == '<select a pipeline>' or selected_pipeline_name == '':
                if self.selected_pipeline is not None:
                    window[self.combobox_key](value= self.selected_pipeline.name)
                return
            if selected_pipeline_name == self.selected_pipeline:
                return

            self.selected_pipeline = self.pipeline_manifest[selected_pipeline_name]

            frame_key = pipeline_key(selected_pipeline_name)
            window[frame_key](visible=True)
            for p in self.pipeline_manifest.list_pipeline_names():
                if p != selected_pipeline_name:
                    window[pipeline_key(p)](visible=False)
        else:
            for pipe_layout in self.config_frames.values():
                if event in pipe_layout.event_keys:
                    pipe_layout.handle(window, event, values)
                    break

    @property
    def layout_name(self):
        return 'Pipeline Selection'
