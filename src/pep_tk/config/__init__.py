ENV_VARIABLE = str
VALUE = str

from pep_tk.config.configurations import PipelineConfig, ConfigOption, PipelineParametersOptionGroup
from pep_tk.config.context import pipeline_environment
from pep_tk.config.pipelines import PipelineManifest

__all__ = ['ConfigOption', 'PipelineConfig', 'PipelineParametersOptionGroup', 'pipeline_environment', 'PipelineManifest', 'ENV_VARIABLE', 'VALUE']