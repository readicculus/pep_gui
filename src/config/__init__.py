import os
from contextlib import contextmanager

from src.datasets import VIAMEDataset
from src.pipelines import PipelineMeta


@contextmanager
def pipeline_environment(pipeline: PipelineMeta, dataset: VIAMEDataset):
    """
        Given a pipeline will set the environment variables required to configure the parameters
        defined for the pipeline in the pipeline_manifest.yaml.
    """
    original_env = os.environ

    cfg = pipeline.config.get_config()
    new_env = {}
    for k, v in cfg.items():
        env_k = v.env_variable
        env_v = v.value()
        new_env[env_k] = str(env_v)

    output_config = pipeline.output_config.get_config()
    for k, v in output_config.items():
        env_k = v.env_variable
        env_v = v.value()
        new_env[env_k] = str(env_v)

    environment_ports = pipeline.dataset_ports.get_env_ports(dataset)
    new_env = {**environment_ports, **new_env}
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


@contextmanager
def dataset_environment(dataset: VIAMEDataset):
    transformation_file_str = 'transformation_file'
    if transformation_file_str in dataset.attributes:
        os.environ['PIPE_ARG_TRANSFORMATION_FILE'] = dataset.attributes[transformation_file_str]
    try:
        yield
    finally:
        if transformation_file_str in os.environ:
            del os.environ[transformation_file_str]
