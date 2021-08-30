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
from typing import List, Optional
import re
import pandas as pd

from pep_tk.core.parser import VIAMEDataset
from pep_tk.core.parser import DuplicateDatasetName, MisingDatasetNameException, ImageListMissingImage, \
    NoImageListException, DatasetFileNotFound, ManifestParser, path_to_absolute



class CSVDatasetsParser(ManifestParser):
    attr_dataset_name = 'dataset_name'

    def __init__(self):
        self._datasets = {}

    def read(self, filename, fullcheck=False):
        cols = [self.attr_dataset_name, self.att_thermal_image_list, self.att_color_image_list,
                                self.att_transform]
        df = pd.read_csv(filename, comment='#', header=0,
                         usecols=cols)[cols]
        df = df.where(pd.notnull(df), None)
        self.validate_dataset_files(filename, df, fullcheck)

    def validate_dataset_files(self, manifeset_fp: str, df: pd.DataFrame, fullcheck):
        read_datasets = {}
        for i, row in df.iterrows():
            ds_name = row.get(self.attr_dataset_name)
            if not ds_name:
                raise MisingDatasetNameException(f'row {i} in {manifeset_fp} does not have a {self.attr_dataset_name}.')
            if ds_name in read_datasets or ds_name in self._datasets:
                raise DuplicateDatasetName(f'Duplicate {self.attr_dataset_name} found "{ds_name}"')
            read_datasets[ds_name] = {self.att_color_image_list: row[self.att_color_image_list],
                                      self.att_thermal_image_list: row[self.att_thermal_image_list],
                                      self.att_transform: row[self.att_transform]}

        manifest_wd = os.path.dirname(manifeset_fp)
        manifeset_fn = os.path.basename(manifeset_fp)

        for ds_name, attrs in read_datasets.items():
            # dataset must have an image list
            if not attrs.get(self.att_thermal_image_list) and not attrs.get(self.att_color_image_list):
                raise NoImageListException(f'[{manifeset_fn}][{ds_name}] ERROR: No color or a thermal image list defined.')

            for a, v in attrs.items():
                if v == None: continue
                datafile_abspath = path_to_absolute(manifest_wd, v)
                datafile_wd = os.path.dirname(datafile_abspath)

                # check that dataset file was found
                if not os.path.isfile(datafile_abspath):
                    raise DatasetFileNotFound(f'[{manifeset_fn}][{ds_name}] ERROR: File "{a}={v}" does not exist.')

                if fullcheck:
                    # check that all images exist in the defined image list
                    if a in [self.att_color_image_list, self.att_thermal_image_list]:
                        with open(datafile_abspath, 'r') as f:
                            image_paths = list(line for line in (l.strip() for l in f.readlines()) if line)
                        for img_fp in image_paths:
                            img_fp = path_to_absolute(datafile_wd, img_fp)
                            if not os.path.isfile(img_fp):
                                raise ImageListMissingImage(
                                    f'[{manifeset_fn}][{ds_name}] ERROR: "{img_fp}" was not found in {a}.')

                # set path to the absolute path
                read_datasets[ds_name][a] = datafile_abspath
        self._datasets.update(read_datasets)

    # given a string, list the dataset keys containing that string
    def list_dataset_keys_txt(self, txt: str) -> List[str]:
        try:
            regkey = '^.*' + txt + '.*$'
            r = re.compile(regkey)
            return list(filter(r.match, self.list_dataset_keys()))
        except:
            return []

    def list_dataset_keys(self) -> List[str]:
        return list(self._datasets.keys())

    def get_dataset(self, name: str) -> Optional[VIAMEDataset]:
        ds = self._datasets.get(name)
        if not ds:
            return None
        return VIAMEDataset(name=name,
                            color_image_list=ds.get(self.att_color_image_list),
                            thermal_image_list=ds.get(self.att_thermal_image_list),
                            transformation_file=ds.get(self.att_transform))
