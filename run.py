from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.shortcuts.progress_bar import formatters
from prompt_toolkit import prompt, HTML
from prompt_toolkit.completion import Completer, Completion
import regex as re

from src import SETUP_VIAME
from src.config import pipeline_environment
from src.kwiver import kwiver_environment
from src.config.configure_pipeline import configure_pipeline
from src.datasets import DatasetManifest, VIAMEDataset
from src.pipelines import PipelineManifest


pipeline_manifest = '/home/yuval/Documents/XNOR/kwiver_batch_runner/conf/pipeline_manifest.yaml'
pipeline_manifest = PipelineManifest(pipeline_manifest)
# parser = DatasetsParser('conf/debug_datasets.yaml')
# datasets = parser.get_dataset('debug:a')
# dataset = datasets['debug:a']
#
pipeline = pipeline_manifest.get_pipeline('JoBBS_seal_yolo_ir_eo_region_trigger')


configure_pipeline(pipeline)

parser = DatasetManifest('conf/datasets.yaml')



class MyCustomCompleter(Completer):
    datasets = parser.get_dataset('.*')
    options = list(datasets.keys())
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        regkey = '^'+text+'.*$'
        for option in self.options:
            if re.match(regkey, option):
            # if option.startswith(option):
                yield Completion(option, start_position=-len(text))

class CLIFlow:
    def start(self):
        self.part1()

    def part1(self):
        datasets_filter = prompt('Select which dataset/s you want to use > ', completer=MyCustomCompleter())
        datasets = parser.get_dataset(datasets_filter)

        while len(datasets) == 0 or not self.part2(datasets):
            datasets_filter = prompt('Select which dataset/s you want to use > ', completer=MyCustomCompleter())
            datasets = parser.get_dataset(datasets_filter)

    def part2(self, selected_datasets):
        print("\nYou've selected the following %d datasets:" % len(selected_datasets))
        for i, ds in enumerate(selected_datasets):
            print('%d: %s' % (i+1, ds))

        confirm = False
        while not confirm:
            res = prompt('\nContinue? Y/N:')
            confirm = res == 'Y'
            if res == 'N':
                return False

        datasets = {dataset_name: VIAMEDataset(dataset_name, attributes) for dataset_name, attributes in
                        selected_datasets.items()}
        return self.part3(datasets)

    def part3(self, datasets):
        with kwiver_environment(SETUP_VIAME), pipeline_environment(pipeline):
            from src.kwiver.embedded_runner import EmbeddedPipelineWorker

            title = HTML('Running %s on <style bg="yellow" fg="black">%d datasets...</style>' %
                         (pipeline.name, len(datasets)))
            custom_formatters = [
                formatters.Label(),
                formatters.Text(" "),
                formatters.Rainbow(formatters.Bar()),
                formatters.Text(" left: "),
                formatters.Rainbow(formatters.TimeLeft()),
            ]
            with ProgressBar(title=title, formatters=custom_formatters) as pb:
                progress_bars = {}
                workers = []
                for name, dataset in datasets.items():
                    worker = EmbeddedPipelineWorker(name,dataset, pipeline.path)
                    label = HTML('<ansired>%s</ansired>: ' % name)
                    progress_bars[name] = pb(range(worker.total), label=label)
                    worker.set_progress_iterator(progress_bars[name])
                    workers.append(worker)

                for w in workers:
                    w.run()







flow = CLIFlow()
flow.start()


