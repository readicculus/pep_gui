from prompt_toolkit.shortcuts import confirm

from src.cli.config_dialog  import ConfigurationPrompt

## configure pipeline
def configure_pipeline(pipeline):
    config = pipeline.config

    answer = confirm("Would you like to modify the pipeline parameter configuration?", suffix='(y/[n])')
    if answer == '': answer = False
    if answer:
        prompt = ConfigurationPrompt(options=config)
        v = prompt.prompt('Use up/down arrow keys to navigate and modify configuration parameters.')

        print(f'you choose: {v}')
