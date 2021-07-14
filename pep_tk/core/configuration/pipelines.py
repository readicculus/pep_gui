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

