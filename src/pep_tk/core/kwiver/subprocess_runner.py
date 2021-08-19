import os
import subprocess
from typing import Dict



def get_pipeline_cmd(debug=False, kwiver_setup_path = None):
    if os.name == 'nt':
        if kwiver_setup_path:
            return [kwiver_setup_path, '&&', 'kwiver.exe', 'runner']
        else:
            return ['kwiver.exe', 'runner']
    else:
        if debug:
            args = ['gdb', '--args', 'kwiver', 'runner']
        else:
            args = ['kwiver', 'runner']

        if kwiver_setup_path:
            args = ['source', kwiver_setup_path, '&&'] + args
        return args

def execute_command(cmd: str, env: Dict, cwd, stdout=None, stderr=None):
    if os.name == 'nt':
        env = {**env, **os.environ}
        return subprocess.Popen(cmd, cwd=cwd,  stdout=stdout, stderr=subprocess.STDOUT, env=env)
    else:
        return subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr, env= env,  shell=True, executable='/bin/bash')


class KwiverRunner:
    '''
        Runner for running non-embedded pipelines that have no input output ports.
        Uses subprocess to call kwiver_runner
    '''
    def __init__(self, pipeline_fp, env, cwd, kwiver_setup_path=None):
        self.pipeline_fp = pipeline_fp
        self.env = env
        self.cwd = cwd
        self.kwiver_setup_path = kwiver_setup_path

    def get_windows_env_str(self):
        env_str = ""
        for k, v in self.env.items():
            env_str += 'SET %s=%s & ' % (k, v) + env_str
        env_str = env_str[:-2]
        return env_str

    def get_linux_env_str(self):
        env_str = ""
        for k, v in self.env.items():
            env_str += '%s=%s ' % (k, v) + env_str
        return env_str

    def run(self, stdout, stderr):
        cmd = get_pipeline_cmd(kwiver_setup_path=self.kwiver_setup_path) + [self.pipeline_fp]
        cmd[0] = f'"{cmd[0]}"'
        cmd = ' '.join(cmd)
        if os.name == 'nt':
            env_str = self.get_windows_env_str()
            print(cmd.replace('&&', '&& ' + env_str))
        else:
            env_str = self.get_linux_env_str()
            print(cmd.replace('&&', '&& ' + env_str) )
        return execute_command(cmd, self.env, self.cwd, stdout=stdout, stderr=stderr)



