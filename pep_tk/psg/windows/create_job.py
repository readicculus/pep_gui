from typing import Dict, Any



def launch_gui():
    import os

    from pep_tk.core.configuration import PipelineManifest
    from pep_tk.core.configuration.exceptions import MissingPortsException
    from pep_tk.core.job import create_job, job_exists
    from pep_tk.core.datasets import DatasetManifest

    from pep_tk.psg.fonts import Fonts
    from pep_tk.psg.windows import initial_setup, run_job, popup_error
    from pep_tk.psg.layouts import DatasetSelectionLayout, PipelineSelectionLayout, LayoutSection
    from pep_tk.psg.settings import get_system_settings, SystemSettingsNames

    import PySimpleGUI as sg

    sg.theme('SystemDefaultForReal')
    setup_window = initial_setup()
    system_settings = get_system_settings()

    pm = PipelineManifest()
    dm = DatasetManifest(manifest_filepath=system_settings[SystemSettingsNames.dataset_manifest_filepath])

    dataset_tab = DatasetSelectionLayout(dm)
    pipeline_tab = PipelineSelectionLayout(pm)

    # ======== Layout helpers =========
    def create_frame(tl: LayoutSection):
        return sg.Frame(layout=tl.get_layout(), title=tl.layout_name, font=Fonts.title_medium, title_color='#0b64c5')

    # ======== Create the Layout =========
    menu_def = [['&File', ['&Resume Job     Ctrl-R::-resume-menu-btn-', '&Properties::-properties-menu-btn-',
                           'E&xit::-exit-menu-btn-']],
                ['&Help', '&About...::-about-menu-btn-'], ]

    layout = [
        [sg.Menu(menu_def, tearoff=False, pad=(200, 1))],
        [sg.Text('Polar Ecosystems Program Batch Runner', size=(38, 1), justification='center', font=Fonts.title_large,
                 relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True, text_color='#063970')]]

    layout += [[create_frame(dataset_tab)],
               [create_frame(pipeline_tab)]]

    layout += [
        [
            sg.Text('Job Name', font=Fonts.description),
            sg.Input('', key='-job_name-IN-', size=(20, 1))
        ]
    ]

    layout += [[sg.Button('Create Job', key='-CREATE_JOB-')]]

    location = (0, 0)
    if SystemSettingsNames.window_location in system_settings.get_dict():
        location = system_settings[SystemSettingsNames.window_location]

    window = sg.Window('PEP-TK: Job Configuration', layout,
                       default_element_size=(12, 1), location=location, finalize=True)
    if setup_window: setup_window.close()

    # ======== Handler helper functions =========
    def validate_inputs(window: sg.Window, values: Dict[Any, Any]) -> bool:
        input_job_name = values['-job_name-IN-']
        combined_job_dir = os.path.join(system_settings.get(SystemSettingsNames.job_directory), input_job_name)
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

    # ======== Window / Event loop =========
    CREATED_JOB_PATH = None
    RESUME_JOB_PATH = None
    RELOAD_GUI = False  # used for when user changes dataset_manifest
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:  # always,  always give a way out!
            break
        try:
            system_settings.set(SystemSettingsNames.window_location, window.CurrentLocation())
        except: pass
        if '::' in event:
            # handle menu button pressed
            menu_event = event.split('::')[1]  # event
            print(menu_event)
            if menu_event == '-resume-menu-btn-':
                initial_folder = system_settings[SystemSettingsNames.job_directory]
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
                dataset_manifest_before = system_settings[SystemSettingsNames.dataset_manifest_filepath]
                setup_window = initial_setup(skip_if_complete=False, modal=True)
                setup_window.close()
                changed_manifest = dataset_manifest_before != system_settings[
                    SystemSettingsNames.dataset_manifest_filepath]
                if changed_manifest:
                    RELOAD_GUI = True
                    break
            elif menu_event == '-exit-menu-btn-':
                break  # exit loop
            continue

        if event == '-CREATE_JOB-':
            if not validate_inputs(window, values):
                continue

            selected_job_directory = values['-job_dir-IN-']
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

        dataset_tab.handle(window, event, values)
        pipeline_tab.handle(window, event, values)
    window.close()
    if RELOAD_GUI:
        launch_gui()
    if CREATED_JOB_PATH:  # END: start running job
        # jc = JobCache(gui_settings)
        # jc.append_job(CREATED_JOB_PATH)
        run_job(CREATED_JOB_PATH)
    elif RESUME_JOB_PATH:
        run_job(RESUME_JOB_PATH)
