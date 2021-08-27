import os
import unittest

from pep_tk.core.configuration import PipelineManifest
from util import CONF_FILEPATH

class TestManifests(unittest.TestCase):
    def test_load_pipeline_manifest(self):
        pm_filepath = os.path.join(CONF_FILEPATH, 'pipeline_manifest.yaml')
        pm = PipelineManifest(manifest_file=pm_filepath)

        pipelines_expeceted = ['polarbear_seal_yolo_ir_eo_region_trigger', 'ir_hotspot_detector', 'eo_seal_detector',
                               'eo_polarbear_detector', 'eo_seal_and_polarbear_detector']
        self.assertListEqual(pipelines_expeceted, pm.list_pipeline_names())

