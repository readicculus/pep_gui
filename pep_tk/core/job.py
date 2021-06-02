import os
import shutil
from typing import List, Dict, Tuple, Optional

import jsonfile

from config import PipelineConfig, PipelineManifest
from config.configurations import PipelineOutputOptionGroup
from datasets import VIAMEDataset
from pep_tk.kwiver.pipeline_compiler import compile_pipeline


class JobInitException(Exception):
    pass


# get job directories / files using the job root dir
meta_dir = lambda root_dir: os.path.join(root_dir, 'meta')
pipelines_dir = lambda root_dir: os.path.join(root_dir, 'pipelines')
job_state_json_fp = lambda root_dir: os.path.join(meta_dir(root_dir), 'job_state.json')
pipeline_meta_json_fp = lambda root_dir: os.path.join(meta_dir(root_dir), 'pipelines_meta.json')
pipeline_manifest_local = lambda root_dir: os.path.join(meta_dir(root_dir), 'pipelines_manifest.yaml')
datasets_meta_json_fp = lambda root_dir: os.path.join(meta_dir(root_dir), 'datasets_meta.json')

class JobMeta:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.pipe_meta_fp = pipeline_meta_json_fp(root_dir)
        self.dataset_meta_fp = datasets_meta_json_fp(root_dir)
        self.compiled_pipelines_dir = pipelines_dir(root_dir) # where the compiled pipelines go
        self._was_existing = os.path.isfile(self.dataset_meta_fp) and os.path.isfile(self.pipe_meta_fp)

        dump_kwargs = dict(ensure_ascii=False, indent="\t", sort_keys=True)
        self._pipe_store = jsonfile.jsonfile(self.pipe_meta_fp, default_data={}, autosave=True, dump_kwargs=dump_kwargs)
        self._ds_store = jsonfile.jsonfile(self.dataset_meta_fp, default_data={}, autosave=True, dump_kwargs=dump_kwargs)

    def create_meta(self, pipeline: PipelineConfig, datasets: List[VIAMEDataset]):
        self._pipe_store.data = pipeline.to_dict()
        for idx, dataset in enumerate(datasets):
            compiled_fp = os.path.join(self.compiled_pipelines_dir, f'{dataset.filename_friendly_name}-{pipeline.name}.pipe')

            # compile ouput ports first so we can cache output information
            output_config = pipeline.output_group.to_dict()
            for config_name, v in output_config.items():
                output_pattern = v['default'].replace('[DATASET]', dataset.filename_friendly_name)
                output_value = os.path.join(self.root_dir, output_pattern)
                output_config[config_name]['_value'] = output_value
                output_config[config_name]['_locked'] = True
            new_output_config = PipelineOutputOptionGroup({'output_config':output_config})

            # compile everything including the new outputs
            env = {**pipeline.get_parameter_env_ports(),
                   **pipeline.get_pipeline_dataset_environment(dataset),
                   **new_output_config.get_env_ports()}
            compiled_pipe = compile_pipeline(pipeline, env)
            with open(compiled_fp, 'w') as f:
                f.write(compiled_pipe)


            self._ds_store.data[dataset.name] = {'compiled_fp': compiled_fp, 'dataset': dataset.to_dict(),
                                                 'output_config': output_config}

    def keys(self):
        return list(self._ds_store.data.keys())

    def get(self, dataset_key) -> Optional[Tuple[str, VIAMEDataset, PipelineOutputOptionGroup]]:
        ds_meta = self._ds_store.data.get(dataset_key)
        if ds_meta is None:
            return None
        pipeline_fp = ds_meta['compiled_fp']
        ds_obj = VIAMEDataset.from_dict(ds_meta['dataset'])
        outputs = PipelineOutputOptionGroup(ds_meta['output_config'])

        return pipeline_fp, ds_obj, outputs

class JobState:
    def __init__(self, root_dir, pipeline_keys=None, load_existing=False):
        self.state_fp = job_state_json_fp(root_dir)

        dump_kwargs = dict(ensure_ascii=False, indent="\t", sort_keys=True)
        self._store = jsonfile.jsonfile(self.state_fp, default_data={}, autosave=True, dump_kwargs=dump_kwargs)

        if load_existing:
            if not os.path.isfile(self.state_fp):
                msg = f'Unable to load job. {self.state_fp} does not exist.'
                raise JobInitException(msg)

            self._store = jsonfile.jsonfile(self.state_fp, default_data={}, autosave=True, dump_kwargs=dump_kwargs)
            if not self._store.data.get('initialized', False):
                msg = f'Possibly corrupt job file, please share the following file with Yuval. {self.state_fp}'
                raise JobInitException(msg)
        else:
            # build the job state cache in the provided directory
            if self._store.data.get('initialized', False):
                raise JobInitException('Job Already Exists, this is a check to make sure jobs cant be overriden.')

            if not pipeline_keys or len(pipeline_keys) < 1:
                raise JobInitException('No pipelines provided.')

            # initialize the new job

            self._store.data['tasks'] = [(i, p) for i, p in enumerate(pipeline_keys)]
            self._store.data['current_task_idx'] = 0
            self._store.data['total_tasks'] = len(pipeline_keys)
            self._store.data['initialized'] = True

    @classmethod
    def load(cls, meta_directory):
        return cls(meta_directory, load_existing=True)

    def get_task(self, idx):
        if idx < 0 or idx >= self._store.data['total_tasks']:
            return None
        for i, t in self.tasks():
            if i == idx:
                return t

        return None

    def current_task(self):
        current_idx = self._store.data['current_task_idx']
        current = self.get_task(current_idx)
        return current

    def increment(self):
        if self._store.data['current_task_idx'] < self._store.data['total_tasks']:
            self._store.data['current_task_idx'] += 1

    def complete(self) -> bool:
        return self._store.data['current_task_idx'] == self._store.data['total_tasks']

    def tasks(self) -> List[Tuple[int, str]]:
        return list(self._store.data['tasks']) # list so that we don't accidentally mutate this

    def completed_tasks(self) -> List[str]:
        completed = []
        current_idx = self._store.data['current_task_idx']
        for i, t in self.tasks():
            if i < current_idx:
                completed.append(t)
        return completed

def load_job(directory: str) -> Tuple[JobState, JobMeta]:
    job_state = JobState.load(directory)
    job_meta = JobMeta(directory)
    return job_state, job_meta


def create_job(directory, pipeline: PipelineConfig, datasets: List[VIAMEDataset]) -> str:
    if os.path.isdir(directory) or os.path.isfile(directory):
        raise Exception('Either directory already exists or is a file an not a directory')

    pipeline_directory = pipelines_dir(directory)
    meta_directory = meta_dir(directory)
    os.makedirs(directory, exist_ok=False)
    os.makedirs(pipeline_directory, exist_ok=False)
    os.makedirs(meta_directory, exist_ok=False)
    try:
        # initialize state and meta
        # TODO make interface for initializing job state and meta the same
        job_meta = JobMeta(directory)
        job_meta.create_meta(pipeline=pipeline, datasets=datasets)
        job_state = JobState(directory, job_meta.keys())
    except Exception as e:
        # clean up if failed for some reason
        # important to make sure this is never reached without the initial directory exists check
        # because we don't wan't to delete a pre-existing job directory
        shutil.rmtree(directory)
        raise e
    return directory
