import abc
import os
import subprocess
import threading
import time
from datetime import datetime

from pep_tk.core.job import JobState, JobMeta, TaskStatus, TaskKey
from pep_tk.util import shell_source
from pep_tk.kwiver.pipeline_compiler import compile_output_filenames
from pep_tk.kwiver.subprocess_runner import KwiverRunner


class SchedulerEventManager(metaclass=abc.ABCMeta):
    def __init__(self):
        self.task_start_time = {}
        self.task_end_time = {}
        self.task_status = {}
        self.task_messages = {}
        self.stdout = {}  # TODO probably issue with storing stdout and stderr for all tasks in memory
        self.stderr = {}
        self.task_count = {}
        self.task_max_count = {}
        self.initialized_tasks = []

    def initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus):
        self.task_count[task_key] = count
        self.task_max_count[task_key] = max_count
        self.task_status[task_key] = status
        self.initialized_tasks.append(task_key)
        self._initialize_task(task_key, count, max_count, status)

    def start_task(self, task_key: TaskKey):
        self.task_status[task_key] = TaskStatus.RUNNING
        self.task_start_time[task_key] = time.time()
        return self._start_task(task_key)

    def end_task(self, task_key: TaskKey, status: TaskStatus):
        self.task_end_time[task_key] = time.time()
        self.task_status[task_key] = status
        return self._end_task(task_key, status)

    def update_task_progress(self, task_key: TaskKey, current_count: int):
        self.task_count[task_key] = current_count
        return self._update_task_progress(task_key, current_count, self.task_max_count[task_key])

    def update_task_stdout(self, task_key: TaskKey, line: str):
        if task_key not in self.stdout:
            self.stdout[task_key] = ""
        self.stdout[task_key] += line
        self._update_task_stdout(task_key, line)

    def update_task_stderr(self, task_key: TaskKey, line: str):
        if task_key not in self.stderr:
            self.stderr[task_key] = ""
        self.stderr[task_key] += line
        self._update_task_stdout(task_key, line)

    def elapsed_time(self, task_key: TaskKey) -> float:
        if task_key not in self.task_start_time:
            return 0.
        if task_key not in self.task_end_time:
            return time.time() - self.task_start_time[task_key]
        return self.task_end_time[task_key] - self.task_start_time[task_key]

    @abc.abstractmethod
    def _initialize_task(self, task_key: TaskKey, count: int, max_count: int, status: TaskStatus):
        return

    @abc.abstractmethod
    def _start_task(self, task_key: TaskKey):
        return

    @abc.abstractmethod
    def _end_task(self, task_key: TaskKey, status: TaskStatus):
        return

    @abc.abstractmethod
    def _update_task_progress(self, task_key: TaskKey, current_count: int, max_count: int):
        return

    @abc.abstractmethod
    def _update_task_stdout(self, task_key: TaskKey, line: str):
        return

    @abc.abstractmethod
    def _update_task_stderr(self, task_key: TaskKey, line: str):
        return


def poll_image_list(fp):
    if not os.path.exists(fp):
        return 0
    with open(fp) as f:
        count = sum(1 for _ in f)
    return count


def monitor_outputs(stop_event: threading.Event, task_key: TaskKey,
                    manager: SchedulerEventManager, output_file: str, poll_freq: int):
    while not stop_event.wait(poll_freq):
        count = poll_image_list(output_file)
        manager.update_task_progress(task_key, count)


class Scheduler:
    progress_poll_freq = 5

    def __init__(self, job_state: JobState, job_meta: JobMeta, manager: SchedulerEventManager, kwiver_setup_path: str):
        self.job_state = job_state
        self.job_meta = job_meta
        self.manager = manager
        self.kwiver_env = shell_source(kwiver_setup_path)

    def run(self):
        # if resuming mark already completed tasks as completed
        for task_key in self.job_state.tasks(status=TaskStatus.SUCCESS):
            pipeline_fp, dataset, outputs = self.job_meta.get(task_key)
            completed_count = max(dataset.thermal_image_count, dataset.color_image_count)
            self.manager.initialize_task(task_key, completed_count, completed_count, TaskStatus.SUCCESS)

        while not self.job_state.is_job_complete():

            current_task_key = self.job_state.current_task()

            pipeline_fp, dataset, outputs = self.job_meta.get(current_task_key)

            max_image_count = max(dataset.thermal_image_count, dataset.color_image_count)

            # Create the environment variables needed for running
            #  - output ports (image list and viame detection csv file names)
            #  - the kwiver environment required for running kwiver runner
            t = datetime.now()
            csv_ports_raw = outputs.get_det_csv_env_ports()
            image_list_raw = outputs.get_image_list_env_ports()

            pipeline_output_csv_env = compile_output_filenames(csv_ports_raw, path=self.job_meta.root_dir, t=t)
            pipeline_output_image_list_env = compile_output_filenames(image_list_raw, path=self.job_meta.root_dir, t=t)

            pipeline_output_env = {**pipeline_output_csv_env, **pipeline_output_image_list_env}
            env = {**pipeline_output_env, **self.kwiver_env}

            # Setup error log
            error_log_fp = os.path.join(self.job_meta.logs_dir,
                                        f'stderr-{current_task_key.replace(":", "_")}.log')
            error_log = open(error_log_fp, 'w+b')

            # Update Task Started
            self.manager.initialize_task(current_task_key, 0, max_image_count, TaskStatus.INITIALIZED)

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
                               env=env)

            process = kwr.run(stdout=subprocess.PIPE, stderr=error_log)

            keep_stdout = True
            stdout = ""

            if process.stdout is None:
                raise RuntimeError("Stdout must not be none")

            # call readline until it returns empty bytes
            for line in iter(process.stdout.readline, b''):
                line_str = line.decode('utf-8')
                self.manager.update_task_stdout(current_task_key, line_str)
                if keep_stdout:
                    stdout += line_str

                # TODO cancel
                # if check_canceled(task, context, force=False):
                #     # Can never be sure what signal a process will respond to.
                #     process.send_signal(signal.SIGTERM)
                #     process.send_signal(signal.SIGKILL)

            # flush logs

            # stop polling for progress
            prog_stop_evt.set()

            # Wait for exit up to 30 seconds after kill
            code = process.wait(30)
            if code > 0:
                error_log.seek(0)
                stderr_log = error_log.read().decode()
                error_log.close()

                # Update Task Ended with error
                count = poll_image_list(image_list_monitor)
                self.manager.update_task_progress(current_task_key, count)
                self.job_state.set_task_status(current_task_key, TaskStatus.ERROR)
                self.manager.update_task_stderr(current_task_key, stderr_log)
                self.manager.end_task(current_task_key, TaskStatus.ERROR)

                # TODO show error in UI, and save in log somewhere
                # raise RuntimeError(
                #     'Pipeline exited with nonzero status code {}: {}'.format(
                #         process.returncode, stderr_log
                #     )
                # )
            else:
                # Update Task Ended with success
                count = poll_image_list(image_list_monitor)
                self.manager.update_task_progress(current_task_key, count)
                self.job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)
                self.manager.end_task(current_task_key, TaskStatus.SUCCESS)

            error_log.close()
