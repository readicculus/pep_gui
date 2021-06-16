ENV_VARIABLE = str
VALUE = str

from pep_tk.core.configuration.configurations import PipelineConfig, ConfigOption, PipelineParametersOptionGroup
from pep_tk.core.configuration.pipelines import PipelineManifest

__all__ = ['ConfigOption', 'PipelineConfig', 'PipelineParametersOptionGroup', 'PipelineManifest', 'ENV_VARIABLE', 'VALUE']