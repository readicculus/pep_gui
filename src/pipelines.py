import os
import yaml
from src import PLUGIN_PATH
from src.config.parser import PipelineGlobalConfig


class PipelineMeta:
    def __init__(self, name, path, config):
        self.name = name
        self.path = os.path.join(PLUGIN_PATH, path)
        self.config = PipelineGlobalConfig(config)


class PipelineManifest:
    __root = 'PipelineManifest'

    def __init__(self, manifest_file):
        with open(manifest_file, 'r') as stream:
            try: dataset_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc: print(exc)

        data = dataset_yaml[self.__root]

        self.pipelines = {}
        for pipeline_name in data:
            path = data[pipeline_name]['path']
            config = data[pipeline_name]['config']
            self.pipelines[pipeline_name] = PipelineMeta(pipeline_name, path, config)

    def get_pipeline(self, pipeline_name):
        return self.pipelines.get(pipeline_name)