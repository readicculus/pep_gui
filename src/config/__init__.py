import os
from contextlib import contextmanager

from src.pipelines import PipelineMeta


@contextmanager
def pipeline_environment(pipeline: PipelineMeta):
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards
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