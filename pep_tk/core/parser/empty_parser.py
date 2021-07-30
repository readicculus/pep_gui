from typing import Optional, List

from pep_tk.core.parser import ManifestParser
from pep_tk.core.parser import VIAMEDataset


class EmptyParser(ManifestParser):
    def __init__(self, error_message = ""):
        self.error_message = error_message

    def list_dataset_keys_txt(self, txt: str) -> List[str]:
        return []

    def list_dataset_keys(self) -> List[str]:
        return []

    def get_dataset(self, name: str) -> Optional[VIAMEDataset]:
        return None