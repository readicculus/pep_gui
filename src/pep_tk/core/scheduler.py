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

import abc
import atexit
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from time import sleep
from typing import List, Optional, IO

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from pep_tk.core.job import JobState, JobMeta, TaskStatus, TaskKey
from pep_tk.core.kwiver.pipeline_compiler import compile_output_filenames
from pep_tk.core.kwiver.runner import KwiverRunner


class SchedulerEventManager(metaclass=abc.ABCMeta):
    def __init__(self):
        self.task_start_time = {}
        self.task_end_time = {}
        self.task_status = {}
        self.task_messages = {}
        self.task_count = {}
        self.task_max_count = {}
        self.initialized_tasks = []
        self.task_output_files = {}

    def initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus,
                        task_outputs: Optional[List[str]] = None):
        self.task_count[task_key] = count
        self.task_max_count[task_key] = max_count
        self.task_status[task_key] = status
        self.initialized_tasks.append(task_key)
        self._initialize_task(task_key, count, max_count, status)

        if task_outputs:
            self.update_task_output_files(task_key, task_outputs)

    def start_task(self, task_key: TaskKey):
        self.task_status[task_key] = TaskStatus.RUNNING
        self.task_start_time[task_key] = time.time()
        return self._start_task(task_key)

    def end_task(self, task_key: TaskKey, status: TaskStatus):
        self.task_end_time[task_key] = time.time()
        self.task_status[task_key] = status
        return self._end_task(task_key, status)

    def check_cancelled(self, task_key: TaskKey) -> bool:
        return self._check_cancelled(task_key)

    def update_task_progress(self, task_key: TaskKey, current_count: int):
        self.task_count[task_key] = current_count
        return self._update_task_progress(task_key, current_count, self.task_max_count[task_key])

    def update_task_stdout(self, task_key: TaskKey, line: str):
        self._update_task_stdout(task_key, line)

    def update_task_stderr(self, task_key: TaskKey, line: str):
        self._update_task_stdout(task_key, line)

    def update_task_output_files(self, task_key: TaskKey, output_files: List[str]):
        self.task_output_files[task_key] = output_files
        return self._update_task_output_files(task_key, output_files)

    def elapsed_time(self, task_key: TaskKey) -> float:
        if task_key not in self.task_start_time:
            return 0.
        if task_key not in self.task_end_time:
            return time.time() - self.task_start_time[task_key]
        return self.task_end_time[task_key] - self.task_start_time[task_key]

    @abc.abstractmethod
    def _initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus):
        pass

    @abc.abstractmethod
    def _start_task(self, task_key: TaskKey):
        pass

    @abc.abstractmethod
    def _end_task(self, task_key: TaskKey, status: TaskStatus):
        pass

    @abc.abstractmethod
    def _update_task_progress(self, task_key: TaskKey, current_count: int, max_count: int):
        pass

    @abc.abstractmethod
    def _update_task_stdout(self, task_key: TaskKey, line: str):
        pass

    @abc.abstractmethod
    def _update_task_stderr(self, task_key: TaskKey, line: str):
        pass

    @abc.abstractmethod
    def _check_cancelled(self, task_key: TaskKey) -> bool:
        pass

    @abc.abstractmethod
    def _update_task_output_files(self, task_key: TaskKey, output_files: List[str]):
        pass


# Scheduler helpers
def poll_image_list(fp: str):
    if not os.path.exists(fp):
        return 0
    with open(fp, 'r') as f:
        count = sum(1 for _ in f)
    return count


def monitor_outputs(stop_event: threading.Event, task_key: TaskKey, manager: SchedulerEventManager,
                    output_file: str, poll_freq: int):
    while not stop_event.wait(poll_freq):
        try:
            count = poll_image_list(output_file)
            manager.update_task_progress(task_key, count)
        except Exception as e:
            # should not have an issue but this is just to ensure program doesn't crash for user
            # pretty sure the concurrency stuff here is solid, but hard to be certain
            print(e)


def enqueue_output(out, queue, evt: threading.Event, logfile: IO):
    # don't want it to stop on an emty byte(b'') because we need to detect
    # if an empty byte has come through and we can't do it asynchronously
    for line in iter(out.readline, b'foobar'):
        if evt.is_set():
            logfile.close()
            out.close()
            break
        try:
            logfile.write(line)
            queue.put(line)
        except Exception as e:
            # should not have an issue but this is just to ensure program doesn't crash for user
            # pretty sure the concurrency stuff here is solid, but hard to be certain
            print(e)


def move_output_files(output_fps, destination_dir):
    new_files = []
    for current_loc in output_fps:
        if not os.path.isfile(current_loc):
            # handle case where output file doesn't exist (errored before pipeline started)
            continue
        new_loc = os.path.join(destination_dir, os.path.basename(current_loc))
        shutil.move(current_loc, new_loc)
        new_files.append(new_loc)
    return new_files


def exit_cleanup(fds, files_to_move, dir_to_move):
    for f in fds:
        try:
            f.close()
        except:
            print(f'Warning: Unable to close {f.name}')

    move_output_files(files_to_move, dir_to_move)


def kill_process(process):
    if os.name == 'nt':
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])
    else:
        process.kill()


class Scheduler:
    def __init__(self,
                 job_state: JobState,
                 job_meta: JobMeta,
                 manager: SchedulerEventManager,
                 kwiver_setup_path: str,
                 progress_poll_freq: int = 1,
                 kill_event: threading.Event() = None):
        """
        Initialize a Scheduler for proccessing task queue synchronously.

        :param job_state: the job state
        :param job_meta: the job metadata
        :param manager: manager for dispatching events, updating progress, etc..
        :param kwiver_setup_path: setup_viame.sh/bat path
        :param progress_poll_freq: frequency to poll progress (reads output file and counts progress)
        :param kill_event: threading.Event to send the scheduler if the GUI thread is exited or the program is killed
        which will trigger the scheduler to cleanup and exit cleanly
        """
        self.job_state = job_state
        self.job_meta = job_meta
        self.manager = manager
        self.kwiver_setup_path = kwiver_setup_path
        self.progress_poll_freq = progress_poll_freq
        self.kill_event: threading.Event() = kill_event

    def run(self):
        print('Scheduler Started (pid: %d)' % os.getpid())
        # if resuming mark already completed tasks as completed
        for task_key in self.job_state.tasks(status=TaskStatus.SUCCESS):
            pipeline_fp, dataset, outputs = self.job_meta.get(task_key)
            max_image_count = max(dataset.thermal_image_count, dataset.color_image_count)

            # read output log if exists
            stdout_log_fp = os.path.join(self.job_meta.logs_dir,
                                         f'kwiver-output-{task_key.replace(":", "_")}.log')
            if os.path.isfile(stdout_log_fp):
                with open(stdout_log_fp, 'r') as f:
                    log = f.read()
                self.manager.update_task_stdout(task_key,
                                                'Task already complete.  Log file found: %s\n' % stdout_log_fp)
                self.manager.update_task_stdout(task_key, log)

            # initialize the task
            task_outputs = self.job_state.get_task_outputs(task_key)
            self.manager.initialize_task(task_key, max_image_count, max_image_count, TaskStatus.SUCCESS, task_outputs)

        for task_key in self.job_state.tasks():
            status = self.job_state.get_status(task_key)
            if status != TaskStatus.SUCCESS:
                pipeline_fp, dataset, outputs = self.job_meta.get(task_key)
                max_image_count = max(dataset.thermal_image_count, dataset.color_image_count)
                self.manager.initialize_task(task_key, 0, max_image_count, TaskStatus.INITIALIZED)

        while not self.job_state.is_job_complete():
            current_task_key = self.job_state.current_task()
            pipeline_fp, dataset, outputs = self.job_meta.get(current_task_key)

            # Create the environment variables needed for running
            #  - output ports (image list and viame detection csv file names)
            #  - the kwiver environment required for running kwiver runner
            stdout_enqueue_thread = datetime.now()
            csv_ports_raw = outputs.get_det_csv_env_ports()
            image_list_raw = outputs.get_image_list_env_ports()

            pipeline_output_csv_env = compile_output_filenames(csv_ports_raw, path=self.job_meta.pending_outputs_dir,
                                                               t=stdout_enqueue_thread)
            pipeline_output_image_list_env = compile_output_filenames(image_list_raw,
                                                                      path=self.job_meta.pending_outputs_dir,
                                                                      t=stdout_enqueue_thread)

            env = {**pipeline_output_csv_env, **pipeline_output_image_list_env}

            # Setup error log
            stdout_log_fp = os.path.join(self.job_meta.logs_dir,
                                         f'kwiver-output-{current_task_key.replace(":", "_")}.log')

            output_log = open(stdout_log_fp, 'w+b')

            atexit.register(exit_cleanup, fds=[output_log],
                            files_to_move=list(pipeline_output_csv_env.values()) + list(
                                pipeline_output_image_list_env.values()),
                            dir_to_move=self.job_meta.error_outputs_dir)

            # Update Task Started
            self.manager.start_task(current_task_key)
            self.job_state.set_task_status(current_task_key, TaskStatus.RUNNING)

            # create the progress polling thread and start it
            image_list_monitor = list(pipeline_output_image_list_env.values())[0]  # Image list to monitor
            prog_stop_evt = threading.Event()
            thread_args = (prog_stop_evt, current_task_key, self.manager, image_list_monitor, self.progress_poll_freq)
            progress_thread = threading.Thread(target=monitor_outputs,
                                               args=thread_args,
                                               daemon=True)
            progress_thread.start()

            # Create the kwiver runner and run it
            kwr = KwiverRunner(pipeline_fp,
                               cwd=self.job_meta.root_dir,
                               env=env,
                               kwiver_setup_path=self.kwiver_setup_path)

            process = kwr.run(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print('Kwiver Runner Started (pid: %d)' % process.pid)

            if process.stdout is None:
                raise RuntimeError("Stdout must not be none")

            # Stdout Thread
            kwiver_output_queue = Queue()
            stdout_enqueue_thread = threading.Thread(target=enqueue_output, args=(
            process.stdout, kwiver_output_queue, prog_stop_evt, output_log))
            stdout_enqueue_thread.daemon = True  # thread dies with the program
            stdout_enqueue_thread.start()

            cancelled = False
            while not cancelled:  # read line without blocking
                if self.kill_event:
                    if self.kill_event.is_set():
                        # Kill all incomplete tasks
                        self._kill_all_tasks(process, prog_stop_evt)
                        exit_cleanup(fds=[output_log],
                                     files_to_move=list(pipeline_output_csv_env.values()) + list(
                                         pipeline_output_image_list_env.values()),
                                     dir_to_move=self.job_meta.error_outputs_dir)
                        return
                try:
                    line = kwiver_output_queue.get(timeout=.5)
                    if line == b'':
                        break  # job is complete if empty byte received
                    else:
                        self.manager.update_task_stdout(current_task_key, line.decode("utf-8"))
                except Empty:
                    pass

                # check if user cancelled task, if cancelled kill kwiver process and stop output reading loop
                cancelled = self.manager.check_cancelled(current_task_key)

            # Wait for exit up to 30 seconds after kill
            code = process.wait(30)

            # stop polling for progress and stop polling for stdout
            prog_stop_evt.set()

            outputs_to_move = list(pipeline_output_csv_env.values()) + list(pipeline_output_image_list_env.values())

            # if user cancells task
            if cancelled:
                kill_process(process)
                print(f'Cancelled {current_task_key}')

                count = poll_image_list(image_list_monitor)
                self.manager.update_task_progress(current_task_key, count)
                self.job_state.set_task_status(current_task_key, TaskStatus.CANCELLED)
                self.manager.end_task(current_task_key, TaskStatus.CANCELLED)

                # Move outputs to error folder, attempt until process releases lock on files
                moved = False
                attempts = 0
                while not moved:
                    if attempts > 30:
                        # try for 30 seconds
                        break
                    try:
                        move_output_files(outputs_to_move, self.job_meta.error_outputs_dir)
                        moved = True
                    except PermissionError:
                        sleep(1)
                        attempts += 1

                continue

            if code > 0:  # ERROR
                # Update Task Ended with error
                count = poll_image_list(image_list_monitor)
                self.manager.update_task_progress(current_task_key, count)
                self.job_state.set_task_status(current_task_key, TaskStatus.ERROR)
                self.manager.end_task(current_task_key, TaskStatus.ERROR)

                # Move output files to error dir
                outputs_to_move = list(pipeline_output_csv_env.values()) + list(pipeline_output_image_list_env.values())
                move_output_files(outputs_to_move, self.job_meta.error_outputs_dir)
            else:  # SUCCESS
                # Update Task final count in GUI, has to be done before moving file
                count = poll_image_list(image_list_monitor)
                self.manager.update_task_progress(current_task_key, count)

                # Move outputs to completed folder
                outputs_new_loc = move_output_files(outputs_to_move, self.job_meta.completed_outputs_dir)

                # Update Task State with success and output files
                self.job_state.set_task_outputs(current_task_key, outputs_new_loc)
                self.job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)

                # Update GUI with success
                self.manager.end_task(current_task_key, TaskStatus.SUCCESS)
                self.manager.update_task_output_files(current_task_key, outputs_new_loc)


    def _kill_all_tasks(self, process: subprocess.Popen, prog_stop_evt: threading.Event):
        for task_to_end in self.job_state.tasks():
            if self.job_state.is_task_complete(task_to_end):
                continue  # do not modify state of complete tasks

            # set all tasks statuses to cancelled
            self.job_state.set_task_status(task_to_end, TaskStatus.ERROR)
            self.manager.end_task(task_to_end, TaskStatus.ERROR)
        prog_stop_evt.set()
        process.kill()
        process.wait(timeout=30)