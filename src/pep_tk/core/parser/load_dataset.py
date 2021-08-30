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
from typing import Optional, Tuple

from pep_tk.core.parser import CSVDatasetsParser, INIDatasetsParser, ParserNotFoundException
from pep_tk.core.parser import DatasetManifestError, ManifestParser



def load_dataset_manifest(manifest_fp) -> ManifestParser:
    """
    :returns a ManifestParser
    """
    if manifest_fp is None:
        raise DatasetManifestError('No Manifest given')
    if not os.path.isfile(manifest_fp):
        str = f'Dataset manifest file "{manifest_fp}" does not exist.'
        raise DatasetManifestError(str)

    if manifest_fp.endswith('.csv'):
        dm = CSVDatasetsParser()
    elif manifest_fp.endswith('.cfg') or manifest_fp.endswith('.ini'):
        dm = INIDatasetsParser()
    else:
        raise ParserNotFoundException(
            f'Invalid manifest file format.  Can take csv(.csv) format, or ini format (.ini or .cfg).\n'
            f'"{manifest_fp}"')
    dm.read(manifest_fp)
    return dm


def safe_load_dataset_manifest(manifest_fp) -> Tuple[Optional[ManifestParser], Optional[str]]:
    try:
        dm = load_dataset_manifest(manifest_fp)
        return dm, None
    except DatasetManifestError as e:
        if hasattr(e, 'message'):
            msg = f'Error Type: {e.__class__.__name__}\nMessage:\n{e.message}'
        else:
            msg = str(e)
        return None, msg
    except Exception as e:
        if hasattr(e, 'message'):
            msg = f'Error Type: {e.__class__.__name__}\nMessage:\n{e.message}'
        else:
            msg = str(e)
        return None, msg
