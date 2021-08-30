import os
import tarfile
import unittest

import requests

TEST_DIR = os.path.dirname(__file__)
DATA_FILEPATH = os.path.join(TEST_DIR, 'pep_tk-testdata')
CONF_FILEPATH = os.path.join(os.path.dirname(TEST_DIR), 'conf')
print('TEST_DIR %s' % TEST_DIR)
print('DATA_FILEPATH %s' % DATA_FILEPATH)
print('CONF_FILEPATH %s' % CONF_FILEPATH)

def add_src_to_pythonpath():
    import os
    import sys
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
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

    if os.path.isdir('pep_tk-testdata'):
        return
    archive_fn = 'pep_tk-testdata.tar.gz'
    print(f'Downloading {archive_fn} from Google Drive.....')
    download_file_from_google_drive('1C1yNhG0Aoh15IAG7QU2bUrT6X299j1VL', archive_fn)
    print(f'Extracting archive.')
    with tarfile.open(archive_fn) as tar:
        tar.extractall(path='.')

    print(f'Cleaning up, removing {archive_fn}.')
    os.remove(archive_fn)

    print('DEBUG listdir .')
    print(os.listdir('.'))
    print('DEBUG listdir pep_tk-testdata')
    print(os.listdir('.'))


class TestCaseRequiringTestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        download_dummy_data()

    @classmethod
    def tearDownClass(cls) -> None:
        pass