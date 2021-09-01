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
import shutil

from util import add_src_to_pythonpath, TestCaseRequiringTestData, CONF_FILEPATH, TESTDATA_DIR

add_src_to_pythonpath()

from pep_tk.core.configuration import PipelineManifest
from pep_tk.core.parser import load_dataset_manifest
from pep_tk.core.job import create_job, load_job, TaskStatus


class TestJobState(TestCaseRequiringTestData):
    pm_filepath = os.path.join(CONF_FILEPATH, 'pipeline_manifest.yaml')

    def get_pipeline_and_datasets(self):
        manifest_fp = os.path.join(TESTDATA_DIR, 'datasets_manifest.csv')
        dm = load_dataset_manifest(manifest_fp)
        pm = PipelineManifest(manifest_file=self.pm_filepath)

        datasets = [dm.get_dataset(k) for k in dm.list_dataset_keys()]
        pipeline = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        return pipeline, datasets

    def test_job_directory_structure(self):
        pipeline, datasets = self.get_pipeline_and_datasets()
        job_dir = os.path.join(self.temp_dir, 'jobs')
        created_job_path = create_job(pipeline=pipeline, datasets=datasets, directory=job_dir)

        self.assertIsDir(created_job_path)
        self.assertIsDir(os.path.join(created_job_path, 'meta'))
        self.assertIsDir(os.path.join(created_job_path, 'logs'))
        self.assertIsDir(os.path.join(created_job_path, 'pipelines'))
        self.assertIsFile(os.path.join(created_job_path, 'pipelines',
                                       'Kotz-2019-fl04-cent-polarbear_seal_yolo_ir_eo_region_trigger.pipe'))
        self.assertIsFile(os.path.join(created_job_path, 'pipelines',
                                       'Kotz-2019-fl04-left-polarbear_seal_yolo_ir_eo_region_trigger.pipe'))
        shutil.rmtree(created_job_path)

    def test_job_state(self):
        pipeline, datasets = self.get_pipeline_and_datasets()
        job_dir = os.path.join(self.temp_dir, 'jobs')
        created_job_path = create_job(pipeline=pipeline, datasets=datasets, directory=job_dir)

        job_state, job_meta = load_job(created_job_path)
        self.assertEqual('Kotz-2019-fl04-cent', job_state.current_task())

        self.assertFalse(job_state.is_task_complete(job_state.current_task()))  # current task not complete
        self.assertFalse(job_state.is_job_complete())  # job not complete

        current_task_status = job_state.get_status(job_state.current_task())
        self.assertEqual(TaskStatus.INITIALIZED, current_task_status)

        current_task_key = job_state.current_task()
        job_state.set_task_status(current_task_key, TaskStatus.RUNNING)
        self.assertEqual(current_task_key, job_state.current_task())  # ensure running is still current task

        job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)
        self.assertNotEqual(current_task_key, job_state.current_task())  # ensure running is still current task

        self.assertTrue(job_state.is_task_complete(current_task_key))  # current task not complete
        self.assertFalse(job_state.is_job_complete())  # job not complete

        current_task_key = job_state.current_task()
        job_state.set_task_status(current_task_key, TaskStatus.RUNNING)
        self.assertEqual(current_task_key, job_state.current_task())  # ensure running is still current task

        job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)
        self.assertNotEqual(current_task_key, job_state.current_task())  # ensure running is still current task

        self.assertTrue(job_state.is_task_complete(current_task_key))  # current task not complete
        self.assertTrue(job_state.is_job_complete())  # job not complete

        shutil.rmtree(created_job_path)

    def test_job_state_resume(self):
        # test that modifying job state then resuming maintains correct state
        pipeline, datasets = self.get_pipeline_and_datasets()
        job_dir = os.path.join(self.temp_dir, 'jobs')
        created_job_path = create_job(pipeline=pipeline, datasets=datasets, directory=job_dir)

        job_state, job_meta = load_job(created_job_path)
        current_task_key = job_state.current_task()
        del job_state

        job_state, job_meta = load_job(created_job_path)
        self.assertEqual(current_task_key, job_state.current_task())

        # Set the task status to RUNNING, re-load job_state and ensure task is still not considered completed
        job_state.set_task_status(current_task_key, TaskStatus.RUNNING)
        del job_state
        job_state, job_meta = load_job(created_job_path)
        self.assertEqual(current_task_key, job_state.current_task())
        self.assertFalse(job_state.is_task_complete(current_task_key))
        self.assertEqual(TaskStatus.INITIALIZED, job_state.get_status(current_task_key))

        # Set the task status to SUCCESS, re-load job_state and ensure task is still not considered completed
        job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)
        del job_state
        job_state, job_meta = load_job(created_job_path)
        self.assertNotEqual(current_task_key, job_state.current_task())
        self.assertTrue(job_state.is_task_complete(current_task_key))
        self.assertTrue(1, len(job_state.completed_tasks()))
        self.assertEqual('Kotz-2019-fl04-cent', job_state.completed_tasks()[0])
        self.assertEqual(TaskStatus.SUCCESS, job_state.get_status(current_task_key))

        # Set the task status to RUNNING, re-load job_state and ensure task is still not considered completed
        current_task_key = job_state.current_task()
        job_state.set_task_status(current_task_key, TaskStatus.RUNNING)
        del job_state
        job_state, job_meta = load_job(created_job_path)
        self.assertEqual(current_task_key, job_state.current_task())
        self.assertFalse(job_state.is_task_complete(current_task_key))
        self.assertEqual(TaskStatus.INITIALIZED, job_state.get_status(current_task_key))

        # Set the task status to SUCCESS, re-load job_state and ensure task is still not considered completed
        job_state.set_task_status(current_task_key, TaskStatus.SUCCESS)
        del job_state
        job_state, job_meta = load_job(created_job_path)
        self.assertNotEqual(current_task_key, job_state.current_task())
        self.assertTrue(job_state.is_task_complete(current_task_key))
        self.assertTrue(2, len(job_state.completed_tasks()))
        self.assertListEqual(['Kotz-2019-fl04-cent', 'Kotz-2019-fl04-left'], job_state.completed_tasks())
        self.assertEqual(TaskStatus.SUCCESS, job_state.get_status(current_task_key))

        self.assertTrue(job_state.is_job_complete())
