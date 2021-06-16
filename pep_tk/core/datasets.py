import os
from typing import Optional, List, Dict, Union, Callable

import regex as re
import yaml

from pep_tk.core.util import glob2re


DatasetProperty = Optional[str]

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

class VIAMEDataset:
    def __init__(self, dataset_name, attributes):
        self.name = dataset_name
        self.__attributes__ = attributes
        self.__data__: Dict[str, Callable] = {
            'thermal_image_list': lambda : self.thermal_image_list,
            'color_image_list': lambda : self.color_image_list,
            'transformation_file': lambda : self.transformation_file,
            'color_images': lambda: self.color_images,
            'thermal_images': lambda: self.thermal_images
        }

    def get(self, item: str, default=None):
        return self.__attributes__.get(item, default)

    def __getitem__(self, item: str) -> Union[str, ImageList]:
        return self.__data__[item]()

    def __contains__(self, item):
        return item in self.__data__

    @property
    def filename_friendly_name(self):
        return self.name.replace(DatasetManifest.key_sep, '_')

    @property
    def color_image_list(self) -> DatasetProperty:
        return self.__attributes__.get('color_image_list')

    @property
    def thermal_image_list(self) -> DatasetProperty:
        return self.__attributes__.get('thermal_image_list')

    @property
    def transformation_file(self) -> DatasetProperty:
        return self.__attributes__.get('transformation_file')

    @property
    def thermal_images(self) -> Optional[ImageList]:
        return [] if self.thermal_image_list is None else ImageList(self.thermal_image_list)

    @property
    def color_images(self) ->  Optional[ImageList]:
        return None if self.color_image_list is None else ImageList(self.color_image_list)

    def to_dict(self) -> Dict:
        return {self.name:  self.__attributes__ }

    @property
    def thermal_image_count(self):
        thermal_images = self.thermal_images
        return 0 if thermal_images is None else len(thermal_images)

    @property
    def color_image_count(self):
        color_images = self.color_images
        return 0 if color_images is None else len(color_images)

    @classmethod
    def from_dict(cls, d: Dict):
        keys = list(d.keys())
        assert(len(keys) == 1)
        key = keys[0]
        return cls(key, d[key])

class VIAMEDetectorOutput:
    # TODO ?
    def __init__(self, name, viame_csv_fp, image_list_fp):
        self.name = name
        self.viame_csv_fp = viame_csv_fp
        self.image_list_fp = image_list_fp

class DatasetManifest():
    _root = 'Datasets'
    _dataset_attributes = ['thermal_image_list', 'color_image_list', 'transformation_file']
    key_sep = ':'

    def __init__(self, manifest_filepath: str = 'conf/datasets.yaml'):
        self.manifest_filepath = manifest_filepath
        with open(manifest_filepath, 'r') as stream:
            try: dataset_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc: print(exc)

        self.datasets_data = dataset_yaml[self._root]
        self.dataset_keys = self.list_dataset_keys()

    def list_dataset_keys(self) -> List[str]:
        def parse_recursive(data):
            dataset_keys = []
            for k, v in data.items():
                if any([x in self._dataset_attributes for x in list(v.keys())]):
                    dataset_keys.append(k)
                else:
                    res = parse_recursive(v)
                    for a in res:
                        dataset_keys.append('%s%s%s' % (k, self.key_sep, a))
            return dataset_keys

        return parse_recursive(self.datasets_data)

    def list_dataset_keys_exp(self, exp):
        keys_list_wildcards = []
        regkey = '^'+glob2re(exp)+'$'
        for existing_key in self.dataset_keys:
            if re.match(regkey, existing_key):
                keys_list_wildcards.append(existing_key)

        if len(keys_list_wildcards) == 0:
            msg = '\n'.join(self.dataset_keys)
            print(exp + ' does not exist or does not match any existing datasets.\nFollowing datasets were found:\n' + msg + '\n')
            return []
        return keys_list_wildcards

    def get_dataset(self, path: str) -> Optional[VIAMEDataset]:
        cur = self.datasets_data
        for k in path.split(self.key_sep):
            if k not in cur: return None
            cur = cur[k]
        # TODO: p = path.split(self._key_sep)
        return VIAMEDataset(path, cur)

    def get_datasets(self, key) -> List[VIAMEDataset]:
        """Gets a dataset using a key
        A Key can contain glob expressions, so getting all Kotz datasets the key could be 'Kotz-2019:fl04:*'
        which would return the following.

        {
         "Kotz-2019:fl04:CENT": {
            ...
         },
         "Kotz-2019:fl04:LEFT": {
            ...
         }
        }

        Returns a dictionary of dataset keystrings to datasets
        """
        keys_list_wildcards = self.list_dataset_keys_exp(key)

        out = []
        for wkey in keys_list_wildcards:
            out.append(self.get_dataset(wkey))

        return out

    def __getitem__(self, item) -> VIAMEDataset:
        return self.get_dataset(item)






#
# def align_multimodal_image_lists(list1: ImageList, list2: ImageList, keep_unmatched, max_dist=100):
#     def file_key(fn):
#         fn = os.path.basename(fn)
#         return '_'.join(fn.split('_')[:-1])
#
#     diff = 0
#     aligned = []
#     for i1_idx, i1 in enumerate(list1):
#         i1_key = file_key(i1)
#         found = False
#         for i2_idx, i2 in enumerate(list2[i1_idx:]):
#             i2_idx = i2_idx + i1_idx
#             if i2_idx > i1_idx + max_dist:
#                 continue
#             i2_key = file_key(i2)
#             if i1_key == i2_key:
#                 if i2_idx - i1_idx > diff:
#                     diff = i2_idx - i1_idx
#                     for a in list2[i2_idx - diff:i2_idx]:
#                         aligned.append((None, a))
#                 aligned.append((i1, i2))
#                 found = True
#                 break
#
#         if not found:
#             aligned.append((i1, None))
#
#     if not keep_unmatched:
#         res = []
#         for a,b in aligned:
#             if a is None or b is None:
#                 continue
#             res.append((a,b))
#         return res
#     return aligned