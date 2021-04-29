from prompt_toolkit.shortcuts import confirm

from src.cli.dialogs.configuration import ConfigurationPrompt

## configure pipeline
from src.pipelines import PipelineMeta


def configure_pipeline(pipeline: PipelineMeta):
    config = pipeline.config
    answer = confirm("Would you like to modify the pipeline parameter configuration?", suffix='(y/[n])')
    if answer == '': answer = False
    if answer:
        prompt = ConfigurationPrompt(options=config)
        v = prompt.prompt('Use up/down arrow keys to navigate and modify configuration parameters.')

        print(f'you choose: {v}')
