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
from tests.util import TESTDATA_DIR, TestCaseRequiringTestData, add_src_to_pythonpath

add_src_to_pythonpath()

from pep_tk.core.parser import load_dataset_manifest, DatasetManifestError


class TestDatasetManifests(TestCaseRequiringTestData):
    def test_load_dataset_manifest(self):
        # Test loading the .csv and the .ini manifests
        csv_manifest = os.path.join(TESTDATA_DIR, 'datasets_manifest.csv')
        ini_manifest = os.path.join(TESTDATA_DIR, 'datasets_manifest.cfg')

        dm_csv = load_dataset_manifest(csv_manifest)
        dm_ini = load_dataset_manifest(ini_manifest)
        self.assertListEqual(dm_csv.list_dataset_keys(), dm_ini.list_dataset_keys())

        dataset_keys = dm_csv.list_dataset_keys()
        for k in dataset_keys:
            x = dm_csv.get_dataset(k)
            y = dm_ini.get_dataset(k)
            self.assertEqual(x.transformation_file, y.transformation_file)
            self.assertEqual(x.color_image_count, y.color_image_count)
            self.assertEqual(x.thermal_image_count, y.thermal_image_count)
            self.assertListEqual(x.color_images.files, y.color_images.files)
            self.assertListEqual(x.thermal_images.files, y.thermal_images.files)

    def test_bad_manifest_filepath(self):
        with self.assertRaises(DatasetManifestError) as _:
            load_dataset_manifest('FOOBAR.csv')
        with self.assertRaises(DatasetManifestError) as _:
            load_dataset_manifest('FOOBAR.ini')

    def test_bad_eo_list_filepath(self):
        # Test that a dataset manifest with a bad EO image list path throws an error
        manifest_fp = os.path.join(TESTDATA_DIR, 'datasets_manifest_bad_eolist_fp.csv')
        with self.assertRaises(DatasetManifestError) as context:
            load_dataset_manifest(manifest_fp)

        self.assertTrue('FOOBAR.txt' in context.exception.message)

    def test_bad_ir_list_filepath(self):
        # Test that a dataset manifest with a bad IR image list path throws an error
        manifest_fp = os.path.join(TESTDATA_DIR, 'datasets_manifest_bad_irlist_fp.csv')
        with self.assertRaises(DatasetManifestError) as context:
            load_dataset_manifest(manifest_fp)

        self.assertTrue('FOOBAR.txt' in context.exception.message)

    def test_bad_manifest_duplicate_keys(self):
        # Test that a dataset manifest with duplicate dataset keys throws an error
        manifest_fp = os.path.join(TESTDATA_DIR, 'datasets_manifest_duplicate_keys.csv')
        with self.assertRaises(DatasetManifestError) as context:
            load_dataset_manifest(manifest_fp)

        self.assertTrue('duplicatekey' in context.exception.message)


if __name__ == "__main__":
    unittest.main()
