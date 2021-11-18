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
import threading

from scheduler_test_manager import EventManagerTesting
from util import add_src_to_pythonpath, TESTDATA_DIR, CONF_FILEPATH, TestCaseRequiringSEALTK

add_src_to_pythonpath()

from pep_tk.core.configuration import PipelineManifest
from pep_tk.core.parser import load_dataset_manifest
from pep_tk.psg.settings import get_viame_bash_or_bat_file_path
from pep_tk.core.scheduler import Scheduler
from pep_tk.core.job import TaskStatus, create_job, load_job


class TestJobState(TestCaseRequiringSEALTK):
    pm_filepath = os.path.join(CONF_FILEPATH, 'pipeline_manifest.yaml')

    def get_pipeline_and_datasets(self):
        manifest_fp = os.path.join(TESTDATA_DIR, 'datasets_manifest.csv')
        dm = load_dataset_manifest(manifest_fp)
        pm = PipelineManifest(manifest_file=self.pm_filepath)

        datasets = [dm.get_dataset(k) for k in dm.list_dataset_keys()]
        pipeline = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        return pipeline, datasets

    def get_log(self, logs_dir, task_key):
        log_files = os.listdir(logs_dir)
        for f in log_files:
            if task_key in f:
                return os.path.join(logs_dir, f)
        return None

    def test_event_manager_end_state(self):
        pipeline, datasets = self.get_pipeline_and_datasets()
        job_dir = os.path.join(self.temp_dir, 'jobs')
        created_job_path = create_job(pipeline=pipeline, datasets=datasets, directory=job_dir)

        job_state, job_meta = load_job(created_job_path)
        kill_event = threading.Event()
        manager = EventManagerTesting(job_state.tasks())
        sched = Scheduler(job_state=job_state,
                          job_meta=job_meta,
                          manager=manager,
                          kwiver_setup_path=get_viame_bash_or_bat_file_path(self.sealtk_dir), kill_event=kill_event)
        sched.run()

        for k, start_time in manager.task_start_time.items():
            end_time = manager.task_end_time[k]
            duration = end_time - start_time
            self.print(f'{k} duration {duration}')
            self.assertTrue(duration <= 20)  # shouldn't be more than 20 seconds

        # check tasks successful
        for k, task_status in manager.task_status.items():
            self.assertEqual(TaskStatus.SUCCESS, task_status)

        # Ensure that the log on disk is the same as the log the GUI would receive
        for task_key in manager.tasks:
            log = manager.get_full_log(task_key)
            lf = self.get_log(job_meta.logs_dir, task_key)
            self.assertIsNotNone(lf)

            with open(lf, 'r') as f:
                log_on_disk = ''.join(f.readlines())
            self.assertEqual(log_on_disk ,log)

