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

# from dataclasses import dataclass
#
#
from dataclasses import dataclass

class ImageList:
    def __init__(self, list_file):
        self.files = []
        base_dir = os.path.dirname(list_file)
        with open(list_file) as f:
            data = f.readlines()
            for d in data:
                fn = os.path.normpath(d.strip())
                if not os.path.isabs(fn):
                    fn = os.path.normpath(os.path.join(base_dir, fn))
                self.files.append(fn)
        self.files = sorted(self.files)
        self.current = -1
        self.total = len(self.files)

    def __iter__(self):
        return self

    def __next__(self): # Python 2: def next(self)
        self.current += 1
        if self.current < self.total:
            return self.files[self.current]
        raise StopIteration

    def __getitem__(self, index: int) -> str:
        return self.files[index]

    def __len__(self):
        return len(self.files)

@dataclass
class VIAMEDataset:
    name: str
    thermal_image_list: str
    color_image_list: str
    transformation_file: str
    _thermal_images: ImageList = None
    _color_images: ImageList = None

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, item: str, default=None):
        return getattr(self, item, default)

    def __contains__(self, item):
        return hasattr(self, item)

    @property
    def thermal_images(self):
        if not self._thermal_images:
            if self.thermal_image_list:
                self._thermal_images = ImageList(self.thermal_image_list)
        return self._thermal_images if self._thermal_images else None

    @property
    def color_images(self):
        if not self._color_images:
            if self.color_image_list:
                self._color_images = ImageList(self.color_image_list)
        return self._color_images if self._color_images else None

    @property
    def thermal_image_count(self):
        return 0 if not self.thermal_images else len(self.thermal_images)

    @property
    def color_image_count(self):
        return 0 if self.color_images is None else len(self.color_images)

    @property
    def filename_friendly_name(self):
        def safe_char(c):
            if c.isalnum() or c == '-':
                return c
            else:
                return "_"

        return "".join(safe_char(c) for c in self.name).rstrip("_")

    def asdict(self):
        return {'color_image_list': self.color_image_list,
                'thermal_image_list': self.thermal_image_list,
                'transformation_file': self.transformation_file,
                'name': self.name}

#
import os
from abc import ABC, abstractmethod
from typing import List, Optional


class DatasetManifestError(Exception):
    def __init__(self, message, *args: object) -> None:
        self.message = message
        super().__init__(*args)


class DatasetFileNotFound(DatasetManifestError):
    pass

class DuplicateDatasetName(DatasetManifestError):
    pass

class ImageListMissingImage(DatasetManifestError):
    pass

class ParserNotFoundException(DatasetManifestError):
    pass

class NoImageListException(DatasetManifestError):
    pass

class MisingDatasetNameException(DatasetManifestError):
    pass

def path_to_absolute(cwd, path):
    if os.path.isabs(path):
        return os.path.normpath(path)
    else:
        return os.path.normpath(os.path.join(cwd, path))


class ManifestParser(ABC):
    att_thermal_image_list = 'thermal_image_list'
    att_color_image_list = 'color_image_list'
    att_transform = 'transformation_file'

    @abstractmethod
    def list_dataset_keys_txt(self, txt: str) -> List[str]:
        pass

    @abstractmethod
    def list_dataset_keys(self) -> List[str]:
        pass

    @abstractmethod
    def get_dataset(self, name: str) -> Optional[VIAMEDataset]:
        pass

    def __getitem__(self, item) -> Optional[VIAMEDataset]:
        return self.get_dataset(item)
