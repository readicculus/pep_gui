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
import logging
import os
import pathlib as pl
import shutil
import tarfile
import unittest

import requests


logging.basicConfig(format='%(asctime)s [%(levelname)s][%(name)s] - %(message)s', level=logging.DEBUG)
global_logger = logging.getLogger(f'')

TEST_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(TEST_DIR, 'pep_tk-testdata')
CONF_FILEPATH = os.path.join(os.path.dirname(TEST_DIR), 'conf')
global_logger.debug('TEST_DIR %s' % TEST_DIR)
global_logger.debug('DATA_FILEPATH %s' % TESTDATA_DIR)
global_logger.debug('CONF_FILEPATH %s' % CONF_FILEPATH)

def add_src_to_pythonpath():
    import os
    import sys
    src_dir = os.path.abspath(os.path.normpath(os.path.join(TEST_DIR, "../src")))
    global_logger.debug('Added PYTHONPATH: %s' % src_dir)
    sys.path.insert(0, src_dir)


def download_dummy_data():
    def download_file_from_google_drive(id, destination):
        def get_confirm_token(response):
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    return value

            return None

        def save_response_content(response, destination):
            CHUNK_SIZE = 32768

            with open(destination, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)

        URL = "https://drive.google.com/uc?export=download"

        session = requests.Session()

        response = session.get(URL, params={'id': id}, stream=True)
        token = get_confirm_token(response)

        if token:
            params = {'id': id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)

        save_response_content(response, destination)
        session.close()
    archive_fn = 'pep_tk-testdata.tar.gz'
    archive_fp = os.path.join(TEST_DIR, archive_fn)
    # if os.path.isfile(archive_fp):
    #     os.remove(archive_fp)

    if os.path.isdir(TESTDATA_DIR):
        global_logger.debug('%s already exists.  Skipping download.' % TESTDATA_DIR)
        return
    global_logger.debug(f'Downloading {archive_fn} from Google Drive.....')
    download_file_from_google_drive('1C1yNhG0Aoh15IAG7QU2bUrT6X299j1VL', archive_fn)
    global_logger.debug(f'Extracting archive.')
    with tarfile.open(archive_fn) as tar:
        tar.extractall(path=TEST_DIR)

    global_logger.debug(f'Cleaning up, removing {archive_fn}.')
    # if os.path.isfile(archive_fp):
    #     os.remove(archive_fp)

    global_logger.debug('DEBUG listdir TEST_DIR')
    global_logger.debug(os.listdir(TEST_DIR))
    global_logger.debug('DEBUG listdir DATA_FILEPATH')
    global_logger.debug(os.listdir(TESTDATA_DIR))

class TestCaseBase(unittest.TestCase):
    def assertIsFile(self, path):
        if not pl.Path(path).resolve().is_file():
            raise AssertionError("File does not exist: %s" % str(path))

    def assertIsDir(self, path):
        if not pl.Path(path).resolve().is_dir():
            raise AssertionError("Directory does not exist: %s" % str(path))

    # print to test log
    def print(self, message, loglevel=logging.INFO):
        self.log.log(level=loglevel, msg=message)


    def setUp(self) -> None:
        # self.log = logging.getLogger(f'({self.test_count}) {type(self).__name__}.{self._testMethodName}')
        self.log = logging.getLogger(self.id())
        self.print('Test Started', logging.DEBUG)

    def tearDown(self) -> None:
        try:
            if self._outcome.success:
                self.print('Test Succeeded', logging.DEBUG)
            else:
                self.print('Test Failed', logging.ERROR)
        except:
            pass


class TestCaseRequiringTestData(TestCaseBase):
    temp_dir = os.path.join(os.getcwd(), 'tmp')

    @classmethod
    def setUpClass(cls):
        download_dummy_data()
        if os.path.isdir(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

        os.makedirs(cls.temp_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temp_dir)


import configparser
class TestCaseRequiringSEALTK(TestCaseRequiringTestData):
    test_config = os.path.join(TEST_DIR, 'config.ini')
    def __init__(self, *args, **kwargs):
        super(TestCaseRequiringTestData, self).__init__(*args, **kwargs)
        self.sealtk_dir = ""
        self.is_valid_sealtk_dir = False

        config = configparser.ConfigParser()
        config.read(self.test_config)
        sealtk_directory = config['TestConfig'].get('sealtk_dir')
        self.sealtk_dir = sealtk_directory
        from pep_tk.psg.settings import get_viame_bash_or_bat_file_path

        if sealtk_directory is not None and os.path.isdir(sealtk_directory) and \
                os.path.isfile(get_viame_bash_or_bat_file_path(sealtk_directory)):
            self.is_valid_sealtk_dir = True

    def setUp(self) -> None:
        if not self.is_valid_sealtk_dir:
            self.skipTest(f'TestConfig SEAL-TK directory is not defined or is not a valid seal-tk directory: '
                          f'"{self.sealtk_dir}".\n'
                          f'In order to run tests that actuall run a pipeline SEAL-TK needs to be downloaded. '
                          f'You can find SEAL-TK binaries at https://github.com/VIAME/VIAME/.\n'
                          'To configure the location for tests, change the location of your SEAL-TK directory in '
                          'pep_gui/tests/config.ini')
        else:
            super(TestCaseRequiringTestData, self).setUp()
