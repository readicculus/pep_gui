import os
from typing import Optional, List

import yaml

from config import PipelineConfig
from config.pipelines import PipelineManifest
from pep_tk.datasets import DatasetManifest, VIAMEDataset


class TaskState:
    def __init__(self, fp: str):
        '''
        Loads or if fp does not exist creates a new state.
        :param fp: filepath of the state metadata file
        '''
        self.fp = fp
        self._datasets_completed = []
        self._datasets_queue = []
        self.current = None
        self._locked = 0 # 0 is unlocked 1 is locked

        if not os.path.exists(self.fp):
            self._save_state()
        else:
            self._load_state()

    def set_datasets(self, dataset_names):
        if self._locked:
            raise Exception('Cannot set datasets once a configuration is locked.')

        self._datasets_queue = dataset_names

    def get_datasets(self, dataset_manifest: DatasetManifest):
        res = []
        for dataset_name in self._datasets_queue:
            dataset = dataset_manifest.get_dataset(dataset_name)
            if dataset is None:
                msg = "Tried to load dataset '%s' but it no longer exists in the manifest file: %s" % \
                      (dataset_name, dataset_manifest.manifest_filepath)
                raise Exception(msg)
            res.append(dataset)

        return res

    def mark_dataset_as_completed(self, dataset_name):
        if not dataset_name in self._datasets_queue:
            msg = 'Dataset "%s" not in queue but marked as completed' % dataset_name
            raise Exception(msg)
        if dataset_name in self._datasets_completed:
            msg = 'Dataset "%s" already marked as completed' % dataset_name
            raise Exception(msg)

        self._datasets_completed.remove(dataset_name)
        self._datasets_completed.append(dataset_name)
        self._save_state()

    def lock(self):
        self._locked = 1
        self._save_state()

    def _load_state(self):
        with open(self.fp, 'r') as file:
            res = yaml.load(file, Loader=yaml.FullLoader)
            if res:
                if res.get('datasets_completed'): self._datasets_completed = res.get('datasets_completed')
                if res.get('datasets_queue'): self._datasets_queue = res.get('datasets_queue')
                if res.get('status'): self._locked = res.get('status')

    def _save_state(self):
        d = {'datasets_completed': self._datasets_completed,
             'datasets_queue': self._datasets_queue,
             'status': self._locked}

        with open(self.fp, 'w') as outfile:
            yaml.dump(d, outfile, default_flow_style=False)

    def is_locked(self):
        return self._locked



class TaskContextController:
    __log_dir = 'logs'
    __configs_dir = 'configs'

    def __init__(self, task_dir, pipeline_manifest: PipelineManifest, dataset_manifest: DatasetManifest):

        # session directory where all session files go
        self.task_dir = task_dir
        self.configs_dir = os.path.join(self.task_dir, self.__configs_dir)
        self.pipeline_config_fp = os.path.join(self.configs_dir, 'pipeline_parameters.yaml')
        self.selected_datasets_fp = os.path.join(self.configs_dir, 'selected_datasets.yaml')
        self.task_meta_fp = os.path.join(self.configs_dir, 'task_meta.yaml')

        # setup models
        self.pipeline_manifest = pipeline_manifest
        self.dataset_manifest = dataset_manifest

        # Setup loggers
        os.makedirs(self.configs_dir, exist_ok=True)

        # setup task metadata
        self.state = TaskState(self.task_meta_fp)

        self.selected_pipeline_config: Optional[PipelineConfig] = None
        self.selected_datasets: List[VIAMEDataset] = []

        # if the state already existed then update selected_datasets
        # and selected_pipeline_config to represent the saved information
        if self.state.is_locked():
            self.selected_datasets = self._load_selected_datasets()
            self.selected_pipeline_config = self._load_pipeline_config()

    def select_pipeline(self, pipeline_name):
        if not self.state.is_locked():
            self.selected_pipeline_config = self.pipeline_manifest[pipeline_name]

    def select_datasets(self, datasets_path):
        if not self.state.is_locked():
            self.selected_datasets = self.dataset_manifest.get_datasets(datasets_path)


    def complete_setup(self) -> bool:
        if self.state.is_locked():
            return False
        if len(self.selected_datasets) == 0:
            return False
        if self.selected_pipeline_config is None:
            return False

        self._save_pipeline_config()
        self._save_selected_datasets()

        if not self.state.is_locked():
            self.state.set_datasets([dataset.name for dataset in self.selected_datasets])
            self.state.lock()
        return True

    # Load/Save pipeline config
    def _save_pipeline_config(self):
        if not self.state.is_locked():
            if self.selected_pipeline_config is not None:
                config_dict = self.selected_pipeline_config.to_dict()
                with open(self.pipeline_config_fp, 'w') as outfile:
                    yaml.dump({self.selected_pipeline_config.name: config_dict}, outfile, default_flow_style=False)

    def _load_pipeline_config(self):
        with open(self.pipeline_config_fp, 'r') as f:
            cfg = yaml.safe_load(f)
        pipeline_name, pipeline_cfg = list(cfg.items())[0] # should only ever be one key/value in the dict
        selected_pipeline_config = self.pipeline_manifest.pipelines[pipeline_name]
        selected_pipeline_config.from_dict(pipeline_cfg, lock=True)
        return selected_pipeline_config

    # Load/Save selected dataset information
    def _save_selected_datasets(self):
        if not self.state.is_locked():
            if len(self.selected_datasets) > 0:
                datasets_dict = {}
                for ds in self.selected_datasets:
                    datasets_dict.update(ds.to_dict())
                with open(self.selected_datasets_fp, 'w') as outfile:
                    yaml.dump(datasets_dict, outfile, default_flow_style=False)

    def _load_selected_datasets(self):
        return self.state.get_datasets(self.dataset_manifest)
