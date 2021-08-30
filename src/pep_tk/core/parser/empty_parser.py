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