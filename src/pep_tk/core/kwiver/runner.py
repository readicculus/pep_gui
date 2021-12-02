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
import subprocess
from typing import Dict, List


def get_kwiver_runner_command(kwiver_setup_path=None, debug=False) -> List:
    """
    Get Command for Kwiver Runner

    :param kwiver_setup_path: path to kwiver_setup.sh or on windows kwiver_setup.bat
    :param debug: run kwiver with gdb --debug
    :return: List command
    """
    if os.name == 'nt':
        if kwiver_setup_path:
            return [f'"{kwiver_setup_path}"', '&&', 'kwiver.exe', 'runner']
        else:
            return ['kwiver.exe', 'runner']
    else:
        if debug:
            args = ['gdb', '--args', 'kwiver', 'runner']
        else:
            args = ['kwiver', 'runner']

        if kwiver_setup_path:
            args = ['source', kwiver_setup_path, '&&', 'printenv', '&&'] + args
        return args


def execute_command(cmd: str, env: Dict, cwd, stdout=None, stderr=None) -> subprocess.Popen:
    """
    Executes a command using subprocess.Popen on windows or linux.

    :param cmd: command to run
    :param env: environment
    :param cwd: working directory
    :param stdout: stdout file/stream
    :param stderr: stderr file/stream
    :return: subprocess.Popen object
    """
    if os.name == 'nt':
        env = {**env, **os.environ}
        return subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT, env=env)
    else:
        env = {**env, **os.environ}
        return subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stderr, env=env, shell=True, executable='/bin/bash')


class KwiverRunner:
    """
        Runner for running non-embedded pipelines that have no input output ports.
        Uses subprocess to call kwiver_runner
    """

    def __init__(self, pipeline_fp: str,
                 cwd: str,
                 env: Dict = None,
                 pipe_args: Dict = None,
                 kwiver_setup_path: str = None):
        """

        :param pipeline_fp: Filepath of the .pipe file being run.
        :param cwd: the working directory in which to run the pipeline.
        :param env: environment variables to set when running the pipeline.
        :param pipe_args: arguments to pass to kwiver runner in the '-s process:param=value' format.
        :param kwiver_setup_path: Path to the 'setup_viame.sh' or on windows 'setup_viame.bat'.
        """
        self.pipeline_fp = pipeline_fp
        self.cwd = cwd
        self.kwiver_setup_path = kwiver_setup_path
        self.env = env or {}
        self.pipe_args = pipe_args or {}

    def get_environment_str(self) -> str:
        """
        Creates the environment string that goes before the command to set the environment of the process
        :return: str command to set environment variables on windows or linux
        """
        if os.name == 'nt':
            env_str = ""
            for k, v in self.env.items():
                env_str += 'SET %s=%s & ' % (k, v) + env_str
            env_str = env_str[:-2]
            return env_str
        else:
            env_str = ""
            for k, v in self.env.items():
                env_str += '%s=%s ' % (k, v) + env_str
            return env_str

    def get_arguments_str(self) -> str:
        """
        Get args string

        :return: string of arguments to pass to kwiver runner
        """
        args_str = ""
        for k, v in self.pipe_args.items():
            args_str += '-s %s=%s ' % (k, v)
        return args_str

    def run(self, stdout=None, stderr=None) -> subprocess.Popen:
        """
        Runs the pipeline with the provided configuration and returns the subprocess.Popen object.

        :param stdout: Optional stream for process to write stdout to
        :param stderr: Optional stream for process to write stderr to
        :return: The subprocess.Popen object
        """
        cmd = get_kwiver_runner_command(kwiver_setup_path=self.kwiver_setup_path) + [self.pipeline_fp]
        cmd = ' '.join(cmd)

        # Add kwiver runner pipeline arguments
        pipe_args_str = self.get_arguments_str()
        if len(pipe_args_str) > 0:
            cmd += " " + pipe_args_str

        # Useful to print the command as environment variables being set in Popen we need to be able to reproduce
        # within the command for debugging purposes.
        print(cmd.replace('&&', '&& ' + self.get_environment_str()) + cmd + ' ' + pipe_args_str)
        proc = execute_command(cmd, self.env, self.cwd, stdout=stdout, stderr=stderr)
        return proc
