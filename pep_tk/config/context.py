import os
from contextlib import contextmanager
from config import PipelineConfig
from datasets import VIAMEDataset


@contextmanager
def pipeline_environment(pipeline: PipelineConfig, dataset: VIAMEDataset):
    """
        Given a pipeline will set the environment variables required to configure the parameters
        defined for the pipeline in the pipeline_manifest.yaml.
    """
    original_env = os.environ

    dataset_ports_env = pipeline.get_pipeline_dataset_environment(dataset, missing_ok=False)
    config_env = pipeline.get_pipeline_environment()
    new_env = {**dataset_ports_env, **config_env}
    os.environ.update(new_env)
    try:
        yield
    finally:
        # set environment back to original
        for key, value in original_env.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


