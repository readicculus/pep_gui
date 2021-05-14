ENV_VARIABLE = str
VALUE = str

from config.configurations import PipelineConfig, ConfigOption, PipelineParametersOptionGroup
from config.context import pipeline_environment
from config.pipelines import PipelineManifest

__all__ = ['ConfigOption', 'PipelineConfig', 'PipelineParametersOptionGroup', 'pipeline_environment', 'PipelineManifest', 'ENV_VARIABLE', 'VALUE']