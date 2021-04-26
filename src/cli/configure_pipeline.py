from prompt_toolkit.shortcuts import confirm

from src.cli.config_dialog  import SelectionPrompt



    ## configure pipeline
def configure_pipeline(pipeline):
    config = pipeline.config

    # print('The following default configuration was found for the pipeline: %s' % pipeline.name)
    # for k,v in config.get_config().items():
    #     print('%s: %s' % (k, str(v.value())))
    answer = confirm("Would you like to modify the pipeline parameter configuration?", suffix='(y/[n])')
    if answer == '': answer = False
    if answer:
        prompt = SelectionPrompt(options=config)
        v = prompt.prompt('Use up/down arrow keys to navigate and modify configuration parameters.')

        print(f'you choose: {v}')
