# https://github.com/PySimpleGUI/PySimpleGUI/issues/3058
import os
import PySimpleGUI as sg
from pep_tk.psg.settings import get_user_settings, SystemSettingsNames, get_viame_bash_or_bat_file_path


def validate_opt(window, error_key, check_fn, error_msg, value):
    if value or value != '':
        value = os.path.normpath(value)
        if not check_fn(value):
            window[error_key].Update(error_msg)
            window[error_key](visible=True)
            return False
        else:
            window[error_key].Update('')
            window[error_key](visible=False)
            return True

    window[error_key](value='Cannot be empty.')
    window[error_key](visible=True)
    return False


def initial_setup(skip_if_complete=True, modal=False):
    user_settings = get_user_settings()

    def check_complete():
        if user_settings.get(SystemSettingsNames.viame_directory, None) is None:
            return False
        if user_settings.get(SystemSettingsNames.dataset_manifest_filepath, None) is None:
            return False
        if user_settings.get(SystemSettingsNames.job_directory, None) is None:
            return False
        return True

    manifest_folder = user_settings.get(SystemSettingsNames.dataset_manifest_filepath)

    jobs_dir = user_settings.get(SystemSettingsNames.job_directory)

    if manifest_folder: manifest_folder = os.path.dirname(manifest_folder)
    layout = [[sg.Text('Enter the viame directory:')],
              [sg.Input(user_settings.get(SystemSettingsNames.viame_directory, ''), key='-setup_viame_filepath-IN-'),
               sg.FolderBrowse(initial_folder=user_settings.get(SystemSettingsNames.viame_directory))],
              [sg.T('', visible=False, size=(0, 1), key='-setup_viame_filepath-ERROR-', text_color='red')],

              [sg.Text('Enter the dataset manifest filepath:')],
              [sg.Input(user_settings.get(SystemSettingsNames.dataset_manifest_filepath, ''),
                        key='-dataset_manifest_filepath-IN-'),
               sg.FileBrowse(initial_folder=manifest_folder)],
              [sg.T('', visible=False, size=(0, 1), key='-dataset_manifest_filepath-ERROR-', text_color='red')],

              [sg.Text('Enter the job base directory(directory where all jobs go):')],
              [sg.Input(jobs_dir, key='-job_dir-IN-'),
               sg.FolderBrowse(initial_folder=jobs_dir)],
              [sg.T('', visible=False, size=(0, 1), key='-job_dir-ERROR-', text_color='red', auto_size_text=True)],

              [sg.B('Complete Setup'), sg.B('Exit', key='Exit')]]

    if check_complete() and skip_if_complete:
        return None
    location = user_settings[SystemSettingsNames.window_location] or (0, 0)
    window = sg.Window('PEP-TK: Properties',
                       layout,
                       keep_on_top=True,
                       finalize=True,
                       location=location,
                       modal=modal)

    while True:
        if check_complete() and skip_if_complete:
            break

        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            break
        elif event == 'Complete Setup':
            # Validate job base directory
            job_dir_check_fn = lambda x: os.path.isdir(x)
            jobs_base_dir = values['-job_dir-IN-']
            job_dir_valid = validate_opt(window,
                                         '-job_dir-ERROR-',
                                         job_dir_check_fn,
                                         f'Jobs base directory {jobs_base_dir} does not exist.',
                                         jobs_base_dir)
            if job_dir_valid:
                user_settings[SystemSettingsNames.job_directory] = \
                    os.path.normpath(jobs_base_dir)

            # Validate viame/seal-tk folder
            def viame_check_fn(viame_dir):
                setup_viame_fp = get_viame_bash_or_bat_file_path(viame_dir)
                return os.path.isfile(setup_viame_fp)

            viame_dir_val = values['-dataset_manifest_filepath-IN-']
            viame_dir_msg = f'Invalid VIAME/SEAL-TK directory.  Was unable to find setup_viame.sh(linux) or setup_viame.bat(windows) in the selected directory {viame_dir_val}.',
            viame_dir_valid = validate_opt(window,
                                           '-setup_viame_filepath-ERROR-',
                                           viame_check_fn,
                                           viame_dir_msg,
                                           values['-setup_viame_filepath-IN-'])
            if viame_dir_valid:
                user_settings[SystemSettingsNames.viame_directory] = \
                    os.path.normpath(values['-setup_viame_filepath-IN-'])

            # Validate dataset manifest
            manifest_fp_check_fn = lambda x: os.path.isfile(x)
            manifest_fp_val = values['-dataset_manifest_filepath-IN-']
            manifest_fp_valid = validate_opt(window,
                                             '-dataset_manifest_filepath-ERROR-',
                                             manifest_fp_check_fn,
                                             f'Could not find dataset manifest {manifest_fp_val}.',
                                             values['-dataset_manifest_filepath-IN-'])
            if manifest_fp_valid:
                user_settings[SystemSettingsNames.dataset_manifest_filepath] = \
                    os.path.normpath(values['-dataset_manifest_filepath-IN-'])

            if check_complete():
                break

    window.close()
