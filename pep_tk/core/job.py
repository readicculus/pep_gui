import os
from typing import List

import jsonfile

from config import PipelineConfig
from datasets import VIAMEDataset
from pep_tk.kwiver.pipeline_compiler import compile_pipeline, compile_pipeline_files


class JobInitException(Exception):
    pass

class PipelineData:
    pipeline_compiled_file = None
    pipeline_dataset = None
    pipeline_config = None

class JobState:
    def __init__(self, meta_file, pipeline_files=None, load_existing=False):
        self.meta_file = meta_file

        dump_kwargs = dict(ensure_ascii=False, indent="\t", sort_keys=True)
        self._store = jsonfile.jsonfile(self.meta_file, default_data={}, autosave=True, dump_kwargs=dump_kwargs)

        if load_existing:
            if not os.path.isfile(meta_file):
                msg = f'Unable to load job. {meta_file} does not exist.'
                raise JobInitException(msg)

            self._store = jsonfile.jsonfile(self.meta_file, default_data={}, autosave=True, dump_kwargs=dump_kwargs)
            if not self._store.data.get('initialized', False):
                msg = f'Possibly corrupt job file, please share the following file with Yuval. {meta_file}'
                raise JobInitException(msg)
        else:
            # build the job state cache in the provided directory
            if self._store.data.get('initialized', False):
                raise JobInitException('Job Already Exists, this is a check to make sure jobs cant be overriden.')

            if not pipeline_files or len(pipeline_files) < 1:
                raise JobInitException('No pipelines provided.')

            # initialize the new job

            self._store.data['tasks'] = [(i, p) for i, p in enumerate(pipeline_files)]
            self._store.data['current_task_idx'] = 0
            self._store.data['total_tasks'] = len(pipeline_files)
            self._store.data['initialized'] = True

    @classmethod
    def load(cls, meta_directory):
        return cls(meta_directory, load_existing=True)

    def get_task(self, idx):
        if idx < 0 or idx >= self._store.data['total_tasks']:
            return None
        for i, t in self._store.data['tasks']:
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


# get job directories / files using the job root dir
meta_dir = lambda root_dir: os.path.join(root_dir, 'meta')
pipelines_dir = lambda root_dir: os.path.join(root_dir, 'pipelines')
job_state_json_fp = lambda root_dir: os.path.join(meta_dir(root_dir), 'job_state.json')


def load_job(directory) -> JobState:
    job_state_fp = job_state_json_fp(directory)
    job_state = JobState(job_state_fp, load_existing=True)
    return job_state


def create_job(directory, pipeline: PipelineConfig, datasets: List[VIAMEDataset]) -> JobState:
    pipeline_directory = pipelines_dir(directory)
    meta_directory = meta_dir(directory)
    os.makedirs(pipelines_dir(directory), exist_ok=True)
    os.makedirs(meta_directory, exist_ok=True)

    # Job files
    job_state_fp = job_state_json_fp(directory)

    pipeline_files = compile_pipeline_files(output_dir=pipeline_directory, pipeline=pipeline, datasets=datasets)
    datasets_by_name = {ds.name: ds for ds in datasets}
    job_state = JobState(job_state_fp, list(pipeline_files.values()))
    return job_state
