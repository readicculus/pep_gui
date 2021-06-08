import abc
import os
import subprocess
import time

from pep_tk import shell_source
from pep_tk.kwiver.subprocess_runner import KwiverRunner
from core.job import JobState, JobMeta, TaskStatus, TaskKey
from settings import get_viame_bash_or_bat_file_path


class SchedulerEventManager(metaclass=abc.ABCMeta):
    def __init__(self):
        self.task_start_time = {}
        self.task_end_time = {}
        self.task_status = {}

    def start_task(self, task_key: TaskKey):
        self.task_start_time[task_key] = time.time()
        return self._start_task(task_key)

    def end_task(self, task_key: TaskKey, status: TaskStatus):
        self.task_end_time[task_key] = time.time()
        self.task_status[task_key] = status
        return self._end_task(task_key, status)

    def update_task_progress(self, task_key: TaskKey, progress):
        return self._update_task_progress(task_key, progress)

    def update_task_stdout(self, task_key: TaskKey, log: str):
        return

    @abc.abstractmethod
    def _start_task(self, task_key: TaskKey):
        return

    @abc.abstractmethod
    def _end_task(self, task_key: TaskKey, status: TaskStatus):
        return

    @abc.abstractmethod
    def _update_task_progress(self, task_key: TaskKey, progress):
        return

    @abc.abstractmethod
    def _update_task_stdout(self, task_key: TaskKey, log: str):
        return


class Scheduler:
    def __init__(self, job_state: JobState, job_meta: JobMeta, manager: SchedulerEventManager, kwiver_setup_path: str):
        self.job_state = job_state
        self.job_meta = job_meta
        self.manager = manager
        self.kwiver_env = shell_source(kwiver_setup_path)

    def run(self):
        # if resuming mark already completed tasks as completed
        for task_key in self.job_state.tasks(status=TaskStatus.SUCCESS):
            self.manager.end_task(task_key, TaskStatus.SUCCESS)

        while not self.job_state.is_job_complete():
            current_task_key = self.job_state.current_task()

            # mark task as started
            self.manager.start_task(current_task_key)

            pipeline_fp, dataset, outputs = self.job_meta.get(current_task_key)

            pipeline_outputs = outputs.get_env_ports()
            env = {**pipeline_outputs, **self.kwiver_env}

            error_log_fp = os.path.join(self.job_meta.logs_dir,
                                        f'stderr-{current_task_key.replace(":", "_")}.log')
            error_log = open(error_log_fp, 'w+b')
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
            # Wait for exit up to 30 seconds after kill
            code = process.wait(30)
            if code > 0:
                error_log.seek(0)
                stderr = error_log.read().decode()
                error_log.close()
                self.job_state.set_task_status(current_task_key, TaskStatus.ERROR)
                raise RuntimeError(
                    'Pipeline exited with nonzero status code {}: {}'.format(
                        process.returncode, stderr
                    )
                )
            else:
                self.manager.end_task(current_task_key, TaskStatus.SUCCESS)

            error_log.close()

    def progress(self):
        return {}
        # kwr = KwiverRunner()
        # proc = kwr.run(pipeline.path)
        # while True:
        #     count = poll_file(out_file)
        #     pb.items_completed = count
        #     bars.invalidate()
        #     if count == num_items:
        #         break
        #     sleep(5)
        # pb.done = True
        # os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        # x = 1

    def _poll_file(fp):
        if not os.path.exists(fp):
            return 0
        with open(fp) as f:
            count = sum(1 for _ in f)
        return count
