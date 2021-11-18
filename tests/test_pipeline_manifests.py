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
import unittest

from util import CONF_FILEPATH, add_src_to_pythonpath, TESTDATA_DIR, TestCaseBase

add_src_to_pythonpath()

from pep_tk.core.configuration import PipelineManifest
from pep_tk.core.parser import load_dataset_manifest
from pep_tk.core.configuration.exceptions import MissingPortsException


class TestPipelineManifest(TestCaseBase):
    pm_filepath = os.path.join(CONF_FILEPATH, 'pipeline_manifest.yaml')

    def test_load_pipeline_manifest(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)

        pipelines_expeceted = ['polarbear_seal_yolo_ir_eo_region_trigger', 'ir_hotspot_detector', 'eo_seal_detector',
                               'eo_polarbear_detector', 'eo_seal_and_polarbear_detector']
        self.assertListEqual(pipelines_expeceted, pm.list_pipeline_names())

        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        self.assertEqual('polarbear_seal_yolo_ir_eo_region_trigger', dual_stream_pipe.name)
        # TODO: make path checking work on windows
        self.print('dual_stream_pipe.directory: %s' % dual_stream_pipe.directory)
        # expected_dir = os.path.join('pep_gui', 'conf', 'pipelines', 'VIAME-JoBBS-Models', 'dual_stream')
        # self.assertTrue(expected_dir in dual_stream_pipe.directory)

    def test_pipeline_output_group(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']

        self.assertEqual(4, len(dual_stream_pipe.output_group.options))
        configs_expected = ['output_optical_image_list', 'output_optical_detections', 'output_thermal_image_list',
                            'output_thermal_detections']
        for config_opt in dual_stream_pipe.output_group.options:
            self.assertIn(config_opt.name, configs_expected)

    def test_pipeline_parameters_group(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']

        self.assertEqual(6, len(dual_stream_pipe.parameters_group.options))
        configs_expected = ['trigger_threshold', 'seal_max_subregion_count', 'polar_bear_max_subregion_count',
                            'detection_threshold_seal',
                            'detection_threshold_polar_bear', 'detection_threshold_hotspot']
        for config_opt in dual_stream_pipe.parameters_group.options:
            self.assertIn(config_opt.name, configs_expected)

    def test_pipeline_dataset_ports(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        ports = pm['polarbear_seal_yolo_ir_eo_region_trigger'].dataset_ports
        expected_ports_dict = {'thermal_image_list':
                                   {'dataset_attribute': 'thermal_image_list',
                                    'env_variable': 'PIPE_ARG_THERMAL_INPUT'},
                               'optical_image_list':
                                   {'dataset_attribute': 'color_image_list',
                                    'env_variable': 'PIPE_ARG_OPTICAL_INPUT'},
                               'transform_file':
                                   {'dataset_attribute': 'transformation_file',
                                    'env_variable': 'PIPE_ARG_TRANSFORMATION_FILE'}}
        self.assertDictEqual(expected_ports_dict, ports.to_dict())

    def test_dual_stream_dataset_with_dual_stream_pipeline_ports(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        ports = pm['polarbear_seal_yolo_ir_eo_region_trigger'].dataset_ports

        csv_manifest = os.path.join(TESTDATA_DIR, 'datasets_manifest.csv')
        dm = load_dataset_manifest(csv_manifest)
        dataset = dm.get_dataset('Kotz-2019-fl04-cent')

        # Test with dataset that has all matching ports
        res = ports.get_env_ports(dataset)
        self.assertListEqual(list(res.keys()),
                             ['PIPE_ARG_THERMAL_INPUT', 'PIPE_ARG_OPTICAL_INPUT', 'PIPE_ARG_TRANSFORMATION_FILE'])
        for k, v in res.items():
            self.assertTrue(os.path.isabs(v))

    def test_single_stream_dataset_with_dual_stream_pipeline_ports(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)

        csv_manifest = os.path.join(TESTDATA_DIR, 'datasets_manifest_single_stream.csv')
        dm = load_dataset_manifest(csv_manifest)
        dataset = dm.get_dataset('ir-only')
        with self.assertRaises(MissingPortsException) as context:
            pm['polarbear_seal_yolo_ir_eo_region_trigger'].dataset_ports.get_env_ports(dataset)

        self.assertEqual('This pipeline requires [\'color_image_list\'], which was not defined in the dataset ir-only.',
                         context.exception.message)

        p = pm['polarbear_seal_yolo_ir_eo_region_trigger'].dataset_ports.get_env_ports(dataset, missing_ok=True)
        self.assertIsNone(p['PIPE_ARG_OPTICAL_INPUT'])

    def test_single_stream_dataset_with_single_stream_pipeline(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)

        csv_manifest = os.path.join(TESTDATA_DIR, 'datasets_manifest_single_stream.csv')
        dm = load_dataset_manifest(csv_manifest)
        dataset = dm.get_dataset('ir-only')
        pm['ir_hotspot_detector'].dataset_ports.get_env_ports(dataset)

    def test_dual_stream_dataset_with_single_stream_pipeline(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)

        csv_manifest = os.path.join(TESTDATA_DIR, 'datasets_manifest.csv')
        dm = load_dataset_manifest(csv_manifest)
        dataset = dm.get_dataset('Kotz-2019-fl04-cent')
        pm['ir_hotspot_detector'].dataset_ports.get_env_ports(dataset)


class TestPipelineConfigOptionGroup(unittest.TestCase):
    pm_filepath = os.path.join(CONF_FILEPATH, 'pipeline_manifest.yaml')

    def test_group_reset_to_default(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']

        # set to .3
        dual_stream_pipe.parameters_group.get_config_option('trigger_threshold').set_value('.3')
        self.assertEqual(0.3, dual_stream_pipe.parameters_group.get_config_option('trigger_threshold').value())

        # reset using reset_config_option(name)
        dual_stream_pipe.parameters_group.reset_config_option('trigger_threshold')
        self.assertEqual(0.1, dual_stream_pipe.parameters_group.get_config_option('trigger_threshold').value())

        # set to .3
        dual_stream_pipe.parameters_group.get_config_option('trigger_threshold').set_value('.3')
        self.assertEqual(0.3, dual_stream_pipe.parameters_group.get_config_option('trigger_threshold').value())

        # reset using reset_all
        dual_stream_pipe.parameters_group.reset_all()
        self.assertEqual(0.1, dual_stream_pipe.parameters_group.get_config_option('trigger_threshold').value())

class TestPipelineConfigOption(unittest.TestCase):
    pm_filepath = os.path.join(CONF_FILEPATH, 'pipeline_manifest.yaml')

    def test_pipeline_config_initalized(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        c = dual_stream_pipe.parameters_group.get_config_option('trigger_threshold')
        expected = {'name': 'trigger_threshold',
                    '_value': 0.1,
                    '_locked': False,
                    'default': 0.1,
                    'type': 'float[0,1]',
                    'env_variable': 'PIPE_ARG_TRIGGER_THRESHOLD',
                    'description': 'Threshold required for a thermal detection to trigger detection on the color image region.'}
        self.assertDictEqual(c.to_dict(), expected)

    def test_pipeline_config_set_value(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        c = dual_stream_pipe.parameters_group.get_config_option('trigger_threshold')
        c.set_value('.3')
        self.assertEqual(0.3, c.value())
        c.set_value(.3)
        self.assertEqual(0.3, c.value())
        self.assertFalse(c.set_value(2))
        self.assertEqual(0.3, c.value())

    def test_pipeline_config_set_value_locked(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        c = dual_stream_pipe.parameters_group.get_config_option('trigger_threshold')
        c._locked = True
        self.assertFalse(c.set_value(0.3))
        self.assertEqual(c.default, c.value())

    def test_pipeline_config_reset_to_default(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        c = dual_stream_pipe.parameters_group.get_config_option('trigger_threshold')
        c.set_value('.3')
        self.assertEqual(0.3, c.value())
        c.reset()
        self.assertEqual(c.default, c.value())

    def test_pipeline_config_mutation(self):
        pm = PipelineManifest(manifest_file=self.pm_filepath)
        dual_stream_pipe = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']
        c = dual_stream_pipe.parameters_group.get_config_option('trigger_threshold')
        c.set_value(0.3)
        self.assertEqual(0.3, c.value())
        val = pm.pipelines['polarbear_seal_yolo_ir_eo_region_trigger']\
            .parameters_group.get_config_option('trigger_threshold').value()
        self.assertEqual(0.3, val)
