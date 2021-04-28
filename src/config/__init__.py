import os
from contextlib import contextmanager

from src.pipelines import PipelineMeta


@contextmanager
def pipeline_environment(pipeline: PipelineMeta):
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