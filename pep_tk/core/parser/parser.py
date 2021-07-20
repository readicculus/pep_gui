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
                fn = d.strip()
                # if list is filenames then append thee base dir
                if os.path.dirname(fn) == '':
                    fn = os.path.join(base_dir, fn)
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

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, item: str, default=None):
        return getattr(self, item, default)

    def __contains__(self, item):
        return hasattr(self, item)

    @property
    def thermal_image_count(self):
        thermal_image_list = self.get(self.thermal_image_list)
        if not thermal_image_list:
            return 0
        thermal_images = ImageList(thermal_image_list)
        return 0 if thermal_images is None else len(thermal_images)

    @property
    def color_image_count(self):
        color_image_list = self.get(self.color_image_list)
        if not color_image_list:
            return 0
        color_images = ImageList(color_image_list)
        return 0 if color_images is None else len(color_images)

    @property
    def filename_friendly_name(self):
        def safe_char(c):
            if c.isalnum():
                return c
            else:
                return "_"

        return "".join(safe_char(c) for c in self.name).rstrip("_")
    #
    #     def __getitem__(self, item: str) -> Union[str, ImageList]:
    #         return self.get(item)
    #

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


class ImageListMissingImage(DatasetManifestError):
    pass


class ParserNotFoundException(DatasetManifestError):
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
