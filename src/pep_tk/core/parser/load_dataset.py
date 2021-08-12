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
        raise DatasetManifestError(f'Dataset manifest file "{manifest_fp}" does not exist.')

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
