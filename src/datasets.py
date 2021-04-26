import os
from typing import List

import yaml
import regex as re

class DatasetManifest():
    root = 'Datasets'
    key_sep = ':'
    dataset_attributes = ['thermal_image_list', 'color_image_list', 'transformation_file']

    def __init__(self, manifest_file):
        with open(manifest_file, 'r') as stream:
            try: dataset_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc: print(exc)

        self.datasets_data = dataset_yaml[self.root]
        self.dataset_keys = self.list_dataset_keys()

    def list_dataset_keys(self):
        def parse_recursive(data):
            dataset_keys = []
            for k, v in data.items():
                if any([x in self.dataset_attributes for x in list(v.keys())]):
                    dataset_keys.append(k)
                else:
                    res = parse_recursive(v)
                    for a in res:
                        dataset_keys.append('%s%s%s' % (k, self.key_sep, a))
            return dataset_keys

        return parse_recursive(self.datasets_data)

    def get_dataset(self, key):
        """Gets a dataset using a key
        A Key can contain regex wildcard expressions, so getting all Kotz datasets the key could be 'Kotz-2019:fl04:.*'
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
        keys_list_wildcards = []
        regkey = '^'+key+'$'
        for existing_key in self.dataset_keys:
            if re.match(regkey, existing_key):
                keys_list_wildcards.append(existing_key)

        if len(keys_list_wildcards) == 0:
            msg = '\n'.join(self.dataset_keys)
            print(key + ' does not exist or does not match any existing datasets.\nFollowing datasets were found:\n' + msg + '\n')
            return {}

        out = {}
        for wkey in keys_list_wildcards:
            cur = self.datasets_data
            for k in wkey.split(self.key_sep):
                cur = cur[k]
            out[wkey] = cur

        return out


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

    def __getitem__(self, index):
        return self.files[index]

    def __len__(self):
        return len(self.files)






class VIAMEDataset:
    __attribute_types_map = {'thermal_image_list': ImageList,
                             'color_image_list': ImageList,
                             'transformation_file': str,
                             'timestamp_format': str}
    def __init__(self, dataset_name, attributes):
        self.dataset_name = dataset_name
        self.attributes = {k:self.__attribute_types_map[k](v) for k,v in attributes.items()}


def align_multimodal_image_lists(list1: ImageList, list2: ImageList):
    def file_key(fn):
        fn = os.path.basename(fn)
        return '_'.join(fn.split('_')[:-1])

    diff = 0
    aligned = []
    for i1_idx, i1 in enumerate(list1):
        i1_key = file_key(i1)
        found = False
        for i2_idx, i2 in enumerate(list2[i1_idx:]):
            i2_idx = i2_idx + i1_idx
            i2_key = file_key(i2)
            if i1_key == i2_key:
                if i2_idx - i1_idx > diff:
                    diff = i2_idx - i1_idx
                    for a in list2[i2_idx - diff:i2_idx]:
                        aligned.append((None, a))
                aligned.append((i1, i2))
                found = True
                break

        if not found:
            aligned.append((i1, None))
    return aligned


# parser = DatasetManifestParser('../conf/datasets.yaml')
# dataset = parser.get_dataset('Kotz-2019:fl04:CENT')
# x=1
# mapper = PipelineMapper('conf/pipeline_mapper.yaml')
# mapper.get_mappings(dataset)
# print(parser.list_dataset_keys())
# print(json.dumps(datasets, indent=1))
# # print(ds.get_datasets(['Kotz-2019:fl04:.*']))
# x=1