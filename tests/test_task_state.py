import os
import shutil
import unittest

import yaml

def read_yaml(fn):
    with open(fn, 'r') as f:
        res = yaml.safe_load(f.read())

    return res

class DummyTaskTest(unittest.TestCase):
    dummy_task_directory = 'dummy_task'
    test_pipeline_name = 'test_pipeline_1'
    def setUp(self):
        self.delete_dummy_task()

    def delete_dummy_task(self):
        # cleanup by deleting the created dummy task directory if it exists
        if os.path.exists(self.dummy_task_directory) and os.path.isdir(self.dummy_task_directory):
            shutil.rmtree(self.dummy_task_directory)

    @classmethod
    def tearDownClass(self):
        self.delete_dummy_task(self)

    def assertYamlDictEqual(self, actual_filepath, expected_yaml_text, message=None):
        expected = yaml.safe_load(expected_yaml_text)
        actual = read_yaml(actual_filepath)
        self.assertDictEqual(expected, actual, message)

class TestTaskState(DummyTaskTest):
    def init_task(self):
        ''' Helper function to initialize a dummy task '''
        from datasets import DatasetManifest
        from config import PipelineManifest
        from archive.task import TaskContextController

        pm = PipelineManifest('dummy_conf/pipeline_manifest.yaml')
        dm = DatasetManifest('dummy_conf/datasets.yaml')
        task = TaskContextController(self.dummy_task_directory, pm, dm)
        return task

    def test_task_state_init(self):
        task = self.init_task()
        # check task_meta.yml is in correct location
        expected_task_meta_fp = os.path.join(self.dummy_task_directory, 'configs', 'task_meta.yaml')
        self.assertEqual(task.task_meta_fp, expected_task_meta_fp)

        # check task_meta.yml is correctly initialized
        with open(expected_task_meta_fp, 'r') as f:
            actual_value = f.read()
        expected_value = 'datasets_completed: []\ndatasets_queue: []\nstatus: 0\n'
        self.assertEqual(actual_value, expected_value)

    def test_task_state_init_twice(self):
        task = self.init_task()
        task = self.init_task()
        with open(task.task_meta_fp, 'r') as f:
            actual_value = f.read()
        expected_value = 'datasets_completed: []\ndatasets_queue: []\nstatus: 0\n'
        self.assertEqual(actual_value, expected_value)

    def test_task_state_lock_when_required_data_not_present(self):
        task = self.init_task()
        res = task.complete_setup()
        self.assertFalse(res)

        # try just setting pipelines
        task.select_pipeline(self.test_pipeline_name)
        res = task.complete_setup()
        self.assertFalse(res)

        # try just setting dataset
        task = self.init_task()
        task.select_datasets('test:a:*')
        res = task.complete_setup()
        self.assertFalse(res)

    def test_task_state_lock_when_required_data_present(self):
        task = self.init_task()
        task.select_datasets('test:a:*')
        task.select_pipeline(self.test_pipeline_name)
        res = task.complete_setup()
        self.assertTrue(res)

    def test_config_files_locked_task(self):
        task = self.init_task()
        task.select_datasets('test:a:*')
        task.select_pipeline(self.test_pipeline_name)
        task.complete_setup()

        # pipeline_parameters test
        expected = \
        '''
        test_pipeline_1:
          output_group:
            output_dummy_detections_csv: '[TIMESTAMP]_[DATASET].csv'
            output_dummy_image_list: '[TIMESTAMP]_[DATASET]_images.txt'
          parameters_group:
            param_float-0-1: 0.1
            param_int_0-1: 1
        '''
        actual_fp = os.path.join(self.dummy_task_directory, 'configs', 'pipeline_parameters.yaml')
        self.assertYamlDictEqual(actual_fp,expected)

        # selected_datasets test
        expected = \
        '''
            test:a:a1:
              color_image_list: dummy_images.txt
              thermal_image_list: dummy_images.txt
              transformation_file: dummy.h5
            test:a:a2:
              color_image_list: dummy_images.txt
              thermal_image_list: dummy_images.txt
              transformation_file: dummy.h5
        '''
        actual_fp = os.path.join(self.dummy_task_directory, 'configs', 'selected_datasets.yaml')
        self.assertYamlDictEqual(actual_fp,expected)

        # task_meta test
        expected = \
        '''
            datasets_completed: []
            datasets_queue:
            - test:a:a1
            - test:a:a2
            status: 1
        '''
        actual_fp = os.path.join(self.dummy_task_directory, 'configs', 'task_meta.yaml')
        self.assertYamlDictEqual(actual_fp,expected)

    def test_modify_locked_task(self):
        task = self.init_task()
        task.select_datasets('test:a:*')
        task.select_pipeline(self.test_pipeline_name)
        task.complete_setup()
        del task

        loaded_task = self.init_task()
        self.assertTrue(loaded_task.state.is_locked())

        self.assertEqual(loaded_task.selected_pipeline_config.task_key, self.test_pipeline_name)
        self.assertEqual(len(loaded_task.selected_datasets), 2)
        self.assertListEqual([ds.task_key for ds in loaded_task.selected_datasets], ['test:a:a1', 'test:a:a2'])

        loaded_task.select_datasets('test:a:a1')
        self.assertListEqual([ds.task_key for ds in loaded_task.selected_datasets], ['test:a:a1', 'test:a:a2'])

        loaded_task.select_pipeline('test_pipeline_2')
        self.assertEqual(loaded_task.selected_pipeline_config.task_key, self.test_pipeline_name)

        # ensure we can't change a configuration because its locked
        loaded_task.selected_pipeline_config.parameters_group.set_config_option('param_int_0-1', 0)
        self.assertEqual(loaded_task.selected_pipeline_config.parameters_group.get_config_option('param_int_0-1').value(), 1)

        # can't save an already completed/locked task
        self.assertFalse(loaded_task.complete_setup())

if __name__ == "__main__":
    unittest.main()