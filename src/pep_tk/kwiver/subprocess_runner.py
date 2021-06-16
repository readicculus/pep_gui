import os
import subprocess
from typing import Dict



def get_pipeline_cmd(debug=False):
    # return ['kwiver', 'pipe-to-dot', '--setup','-p']
    if os.name == 'nt':
        if debug:
            return ['kwiver.exe', 'runner']
        else:
            return ['kwiver.exe', 'runner']
    else:
        if debug:
            return ['gdb', '--args', 'kwiver', 'runner']
        else:
            return ['kwiver', 'runner']


def execute_command(cmd: str, env: Dict, cwd, stdout=None, stderr=None):
    if os.name == 'nt' and stdout is None:
        fnull = open( os.devnull, "w" )
        return subprocess.call(cmd, cwd=cwd,  stdout=fnull, stderr=subprocess.STDOUT, env=env)

    return subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr, env= env,  shell=True)


class KwiverRunner:
    '''
        Runner for running non-embedded pipelines that have no input output ports.
        Uses subprocess to call kwiver_runner
    '''
    def __init__(self, pipeline_fp, env, cwd):
        self.pipeline_fp = pipeline_fp
        self.env = env
        self.cwd = cwd


    def run(self, stdout, stderr):
        cmd = get_pipeline_cmd() + [self.pipeline_fp]
        cmd = ' '.join(cmd)
        print(cmd)
        return execute_command(cmd, self.env, self.cwd, stdout=stdout, stderr=stderr)



