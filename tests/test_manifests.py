import unittest


class TestManifests(unittest.TestCase):
    def test_load_pipeline_manifest(self):
        from config import PipelineManifest
        pm = PipelineManifest('dummy_conf/pipeline_manifest.yaml')
        assert len(pm.pipelines) == 2
        with self.assertRaises(Exception) as context:
            PipelineManifest('dummy_conf/pipeline_manifest_bad.yaml')

    def test_load_dataset_manifest(self):
        from datasets import DatasetManifest
        dm = DatasetManifest('dummy_conf/datasets.yaml')
        self.assertListEqual(dm.dataset_keys, ['test:a:a1', 'test:a:a2', 'test:b:b1', 'test:b:b2', 'c'])

        # test getting a dataset that isn't defined
        nonexistant_dataset = dm.get_dataset('bad')
        self.assertIsNone(nonexistant_dataset)

        # test wildcards
        all_test = [ds.name for ds in dm.get_datasets('test:*')]
        self.assertListEqual(all_test, ['test:a:a1', 'test:a:a2', 'test:b:b1', 'test:b:b2'])

        all_a = [ds.name for ds in dm.get_datasets('test:a:*')]
        self.assertListEqual(all_a, ['test:a:a1', 'test:a:a2'])

        just_one = [ds.name for ds in dm.get_datasets('test:b:b2')]
        self.assertListEqual(just_one, ['test:b:b2'])


if __name__ == "__main__":
    unittest.main()
