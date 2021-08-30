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

import os
from typing import Dict, Any

import PySimpleGUI as sg

from pep_tk.core.configuration import PipelineManifest
from pep_tk.core.configuration.exceptions import MissingPortsException
from pep_tk.core.job import create_job, job_exists
from pep_tk.core.parser import ManifestParser
from pep_tk.psg.fonts import Fonts
from pep_tk.psg.layouts import DatasetSelectionLayout, PipelineSelectionLayout, LayoutSection
from pep_tk.psg.settings import get_user_settings, SystemSettingsNames
from pep_tk.psg.utils import move_window_onto_screen
from pep_tk.psg.windows import show_properties_window, run_job, popup_error, popup_about


# ======== Handler helper functions =========
def validate_inputs(window: sg.Window, values: Dict[Any, Any], dataset_tab, pipeline_tab) -> bool:
    user_settings = get_user_settings()
    input_job_name = values['-job_name-IN-']
    combined_job_dir = os.path.join(user_settings.get(SystemSettingsNames.job_directory), input_job_name)
    input_datasets = dataset_tab.get_selected_datasets()
    input_pipeline = pipeline_tab.get_selected_pipeline()
    w_loc, w_size = window.current_location(), window.size
    # Check if no datasets were selected
    if len(input_datasets) < 1:
        popup_error('No datasets were selected.  Must select one or more datasets above.', w_loc, w_size)
        return False

    # if pipeline_tab.selected_pipeline is None:
    if not pipeline_tab.validate(values):
        popup_error('Either a pipeline isn\'t selected or error in configuration values.', w_loc, w_size)
        return False

    # Check for missing ports(aka if datasets/pipeline are not compatible)
    missing_ports = {}
    for dataset in input_datasets:
        try:
            input_pipeline.get_pipeline_dataset_environment(dataset)
        except MissingPortsException as e:
            missing_ports[e.dataset_name] = e.ports
    if len(missing_ports) > 0:
        msg = "Datasets aren't compatible with the selected pipeline: \n"
        for dataset_name, ports in missing_ports.items():
            msg += "%s: MISSING(%s)\n" % (dataset_name, ', '.join(ports))
        popup_error(msg, w_loc, w_size)
        return False

    # Check if the selected name is an empty string
    if input_job_name == '':
        popup_error('No job name entered', w_loc, w_size)
        return False

    # Check if the job directory(within the base directory) already exists
    if os.path.isdir(combined_job_dir):
        popup_error(f'Job {input_job_name} already exists, cannot override an existing job.\n{combined_job_dir}',
                    w_loc, w_size)
        return False

    return True


# ======== Create Job Window launcher =========
def launch_gui(pm: PipelineManifest, dm: ManifestParser) -> bool:
    sg.theme('SystemDefaultForReal')

    # ======== Page sections =========
    dataset_tab = DatasetSelectionLayout(dm)
    pipeline_tab = PipelineSelectionLayout(pm)

    def create_frame(tl: LayoutSection):
        return sg.Frame(layout=tl.get_layout(), title=tl.layout_name, font=Fonts.title_medium, title_color='#0b64c5')

    # ======== Create the Layout =========
    menu_def = [['&File', ['&Resume Job     Ctrl-R::-resume-menu-btn-', '&Properties::-properties-menu-btn-',
                           'E&xit::-exit-menu-btn-']],
                ['&Tools', '&Validate Datasets::-validate-menu-btn-'],
                ['&Help', '&About...::-about-menu-btn-'], ]

    layout = [
        [sg.Menu(menu_def, tearoff=False, pad=(200, 1))],
        [sg.Text('Polar Ecosystems Program Batch Runner', size=(38, 1), justification='center', font=Fonts.title_large,
                 relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True, text_color='#063970')],
        [create_frame(dataset_tab)],
        [create_frame(pipeline_tab)],
        [sg.Text('Job Name', font=Fonts.description), sg.Input('', key='-job_name-IN-', size=(20, 1))],
        [sg.Button('Create Job', key='-CREATE_JOB-')]]

    user_settings = get_user_settings()
    location = user_settings.get(SystemSettingsNames.window_location, (None, None))
    window = sg.Window('PEP-TK: Job Configuration', layout,
                       default_element_size=(12, 1), location=location, finalize=True)
    # move back on screen if off screen for some reason
    move_window_onto_screen(window)

    # ======== Show Properties window if properties are not valid =========
    out = show_properties_window(skip_if_valid=True)
    if out.all_valid and out.properties_updated:
        window.close()
        return False  # Reload GUI if properties changed
    if not out.all_valid and not out.properties_updated:
        window.close()
        return True  # Don't reload GUI if user doesn't fix properties and exits out

    # ======== Window / Event loop =========
    CREATED_JOB_PATH = None
    RESUME_JOB_PATH = None
    while True:
        event, values = window.read(timeout=2000)
        if event == sg.WIN_CLOSED:  # always,  always give a way out!
            break
        try:
            user_settings.set(SystemSettingsNames.window_location, window.CurrentLocation())
        except:
            pass
        if event == "__TIMEOUT__":
            continue
        # ======== Handle menu button pressed =========
        if '::' in event:
            menu_event = event.split('::')[1]  # event
            if menu_event == '-resume-menu-btn-':
                initial_folder = user_settings[SystemSettingsNames.job_directory]
                location = window.current_location()
                job_folder = sg.popup_get_folder('Select the job directory',
                                                 no_window=True,
                                                 keep_on_top=True,
                                                 initial_folder=initial_folder,
                                                 modal=True,
                                                 location=location)
                if job_folder:
                    exists = job_exists(job_folder)
                    if exists:
                        RESUME_JOB_PATH = job_folder
                        break
                    else:
                        popup_error(f'Job {job_folder} is not a valid job directory.', window.current_location(),
                                    window.size)
            elif menu_event == '-properties-menu-btn-':
                out = show_properties_window(modal=True)
                if out.properties_updated:
                    window.close()
                    return False  # Reload GUI
            elif menu_event == '-exit-menu-btn-':
                break  # exit loop
            elif menu_event == '-about-menu-btn-':
                popup_about(location=window.current_location())
            elif menu_event == '-validate-menu-btn-':
                pass

        # ======== Handle Create Job button pressed =========
        elif event == '-CREATE_JOB-':
            if validate_inputs(window, values, dataset_tab, pipeline_tab):
                selected_job_directory = user_settings.get(SystemSettingsNames.job_directory)
                selected_job_name = values['-job_name-IN-']

                pipeline = pipeline_tab.get_selected_pipeline()
                datasets = dataset_tab.get_selected_datasets()
                try:
                    job_dir = os.path.join(selected_job_directory, selected_job_name)
                    CREATED_JOB_PATH = create_job(pipeline=pipeline, datasets=datasets, directory=job_dir)
                except Exception as e:
                    popup_error(
                        f'There was an error creating the job: \n {str(e)}.\n I would recommend sending this error to Yuval.',
                        window.current_location(), window.size)
                    continue

                break  # END: close window
        else:
            # ======== Handle other user interactions =========
            dataset_tab.handle(window, event, values)
            pipeline_tab.handle(window, event, values)

    window.close()

    if CREATED_JOB_PATH:
        run_job(CREATED_JOB_PATH)
    elif RESUME_JOB_PATH:
        run_job(RESUME_JOB_PATH)

    return True
