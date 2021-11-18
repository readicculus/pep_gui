#      This file is part of the PEP GUI detection pipeline batch running tool
#      Copyright (C) 2021 Yuval Boss yuval@uw.edu
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import re
from typing import Dict

from pep_tk.core.configuration import PipelineConfig
from datetime import datetime

# Unfortunately the kwiver runner pipe-config will not inject environemnt variables
# and the -s flag creates new blocks sometimes instead of injecting setting in-place
# so here we compile a pipeline by basically replacing all $ENV with the intended value
# and also replacing relativepath attributes with their absolute path.
def compile_pipeline(pipeline: PipelineConfig, env: Dict) -> str:
    with open(pipeline.path, 'r') as f:
        pipeline_content = f.read()

    # Inject $ENV{} in pipeline with the intended value
    pipeline_required_env = list(set(re.findall(r"\$ENV{(.*)}", pipeline_content, re.M)))
    # for pipeline_required in pipeline_required_env:
    #     assert (pipeline_required in env)  # TODO: handle

    for k, v in env.items():
        search_str = '$ENV{%s}' % k
        pipeline_content = pipeline_content.replace(search_str, str(v))

    # # Custom pep_tk macro injection
    # pipeline_content = pipeline_content.replace('[DATASET]', dataset.name)  # [DATASET] macro

    # replace relativepath attributes with their absolute path
    relative_paths = list(set(re.findall(r"relativepath.*=\s*(.*)$", pipeline_content, re.M)))
    absolute_paths = {}
    for path in relative_paths:
        absolute_paths[path] = os.path.abspath(os.path.normpath(os.path.join(pipeline.directory, path)))

    for prev, new in absolute_paths.items():
        pipeline_content = pipeline_content.replace(prev, new)

    pipeline_content = re.sub(r"relativepath\s*", '', pipeline_content)
    return pipeline_content


def compile_output_filenames(output_filenames: Dict[str, str], path='', t=None) -> Dict[str, str]:
    out = {}
    t = t if t else datetime.now()
    timestr = t.strftime("%Y%m%d-%H%M%S")
    for k,v in output_filenames.items():
        new_v = v.replace('[TIMESTAMP]', timestr)
        new_v = os.path.join(path, new_v)
        out[k] = os.path.normpath(new_v)
    return out