import os
import re
from config import PipelineConfig
from datasets import VIAMEDataset


# Unfortunately the kwiver runner pipe-config will not inject environemnt variables
# and the -s flag creates new blocks sometimes instead of injecting setting in-place
# so here we compile a pipeline by basically replacing all $ENV with the intended value
# and also replacing relativepath attributes with their absolute path.
def compile_pipeline(pipeline: PipelineConfig, dataset: VIAMEDataset) -> str:
    with open(pipeline.path, 'r') as f:
        pipeline_content = f.read()

    # Inject $ENV{} in pipeline with the intended value
    pipeline_required_env = list(set(re.findall(r"\$ENV{(.*)}", pipeline_content, re.M)))
    env = {**pipeline.get_pipeline_environment(), **pipeline.get_pipeline_dataset_environment(dataset)}
    for pipeline_required in pipeline_required_env:
        assert (pipeline_required in env)  # TODO: handle

    for k, v in env.items():
        search_str = '$ENV{%s}' % k
        pipeline_content = pipeline_content.replace(search_str, str(v))

    # Custom pep_tk macro injection
    pipeline_content = pipeline_content.replace('[DATASET]', dataset.name)  # [DATASET] macro

    # replace relativepath attributes with their absolute path
    relative_paths = list(set(re.findall(r"relativepath.*=\s*(.*)$", pipeline_content, re.M)))
    absolute_paths = {}
    for path in relative_paths:
        absolute_paths[path] = os.path.abspath(os.path.join(pipeline.directory, path))

    for prev, new in absolute_paths.items():
        pipeline_content = pipeline_content.replace(prev, new)

    pipeline_content = re.sub(r"relativepath\s*", '', pipeline_content)
    return pipeline_content
