import abc
import os
import subprocess
import tempfile
from subprocess import Popen

from pep_tk import shell_source
from pep_tk.kwiver.subprocess_runner import KwiverRunner
from core.job import JobState, JobMeta, TaskStatus
from settings import get_viame_bash_or_bat_file_path


class SchedulerEventManager(metaclass=abc.ABCMeta):
    def __init__(self, settings):
        self.settings = settings

    @abc.abstractmethod
    def task_started(self, task_key):
        return

    @abc.abstractmethod
    def task_finished(self, task_key):
        return

    @abc.abstractmethod
    def task_update_progress(self, task_key, progress):
        return

    @abc.abstractmethod
    def task_update_stdout(self, task_key, log: str):
        return


class Scheduler():
    def __init__(self, job_state: JobState, job_meta: JobMeta, manager: SchedulerEventManager):
        self.job_state = job_state
        self.job_meta = job_meta
        self.manager = manager

        fp = get_viame_bash_or_bat_file_path(self.manager.settings)
        self.kwiver_env = shell_source(fp)

    def run(self):
        # if resuming mark already completed tasks as completed
        for task_key in self.job_state.completed_tasks():
            self.manager.task_finished(task_key)

        # TODO, have to be careful not to re pipes that errored forever
        while not self.job_state.is_job_complete():
            current_task_key = self.job_state.current_task()
            self.manager.task_started(current_task_key)

            pipeline_fp, dataset, outputs = self.job_meta.get(current_task_key)

            pipeline_outputs = outputs.get_env_ports()
            env = {**pipeline_outputs, **self.kwiver_env}


            x=1
            error_log_fp = os.path.join(self.job_meta.root_dir, 'logs', f'stderr-{current_task_key.replace(":","_")}.log')
            error_log = open(error_log_fp ,'w+b')
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
                self.manager.task_update_stdout(current_task_key, line_str)
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
                self.job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)
                self.manager.task_finished(current_task_key)

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