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

import yaml

from pep_tk import PLUGIN_PATH
from pep_tk.core.configuration import PipelineConfig
default_manifest = os.path.normpath(os.path.join(PLUGIN_PATH, 'conf/pipeline_manifest.yaml'))

class PipelineManifest:
    __root = 'PipelineManifest'

    def __init__(self, manifest_file: str = default_manifest):
        self.manifest_file = manifest_file
        with open(manifest_file, 'r') as stream:
            try: dataset_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self.pipelines = {}
        for pipeline_name, pipeline_config in dataset_yaml[self.__root].items():
            self.pipelines[pipeline_name] = PipelineConfig(pipeline_name, pipeline_config)

    def list_pipeline_names(self):
        return list(self.pipelines.keys())

    def __getitem__(self, pipeline_name: str) -> PipelineConfig:
        return self.pipelines[pipeline_name]

