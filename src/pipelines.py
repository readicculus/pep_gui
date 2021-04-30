import os
import yaml
from src import PLUGIN_PATH
from src.config.parser import PipelineGlobalConfig, PipelineOutputConfig
from src.config.ports import DatasetEnvPorts


class PipelineMeta:
    def __init__(self, name, path, config, dataset_ports = None, output_config = None):
        self.name = name
        self.path = os.path.join(PLUGIN_PATH, path)
        self.config = PipelineGlobalConfig(config)
        self.dataset_ports = {} if dataset_ports is None else DatasetEnvPorts(dataset_ports)
        self.output_config = PipelineOutputConfig(output_config)

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
            output_config = data[pipeline_name].get('output_config')
            dataset_ports = data[pipeline_name].get('dataset_ports')
            self.pipelines[pipeline_name] = PipelineMeta(pipeline_name, path, config, dataset_ports, output_config)

    def get_pipeline(self, pipeline_name):
        return self.pipelines.get(pipeline_name)