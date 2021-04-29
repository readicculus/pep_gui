#https://github.com/Kitware/kwiver/blob/master/python/kwiver/sprokit/adapters/embedded_pipeline.cxx
import datetime
import os

from kwiver.sprokit.adapters import embedded_pipeline
from kwiver.sprokit.adapters import adapter_data_set
from prompt_toolkit.patch_stdout import patch_stdout

from src.datasets import align_multimodal_image_lists
from src.util.image import load_image_kvr_container, ocv_load
from src.util.image_thread import ImageLoader
from src.util.logging import stderr_redirected


class EmbeddedPipelineRunner:
    def __init__(self, pipeline_file):
        self.pipeline_file = pipeline_file
        self.loaded = False
        self.running = False
        self.input_ports = None
        self.output_ports = None
        self.input_adapter = None

    def load(self):
        self.ep = embedded_pipeline.EmbeddedPipeline()
        # build pipeline
        temp = os.getcwd()
        os.chdir(os.path.dirname(self.pipeline_file))
        self.ep.build_pipeline(self.pipeline_file)
        os.chdir(temp)

        self.input_ports=self.ep.input_port_names()
        self.output_ports=self.ep.input_port_names()

        self.input_adapter = adapter_data_set.AdapterDataSet.create()


        self.loaded = True


    def start(self):
        if not self.loaded:
            raise Exception('Embedded pipeline must be loaded before starting use pipeline_runner.load()')
        self.ep.start()
        self.running = True

    def stop(self):
        if not self.running:
            raise Exception('Called stop and is not currently running.')
        self.ep.stop()
        self.running = False

    def full(self):
        return self.ep.full()

    def send(self, args_dict):
        for k,v in args_dict.items():
            self.input_adapter[k] = v
        self.ep.connect_input_adapter()
        self.ep.send(self.input_adapter)


    def receive(self):

        if self.ep.at_end():
            return None, None
        ads_out = self.ep.receive()
        # print('ep.at_end ' + str(self.ep.at_end()))
        # print('ads_out.is_end_of_data ' + str(ads_out.is_end_of_data()))
        # if ads_out.is_end_of_data():

        dets_ir = ads_out['detected_object_set_ir']
        dets_eo = ads_out['detected_object_set_eo']
        # if len(dets_ir): ir_data.append(dets_ir)
        # if len(dets_eo): eo_data.append(dets_eo)
        return dets_eo, dets_ir


class EmbeddedPipelineWorker:
    def __init__(self, name, dataset, pipeline_fp):
        self.name = name
        self.dataset = dataset
        self.pipeline_fp = pipeline_fp

        self.aligned_images = align_multimodal_image_lists(self.dataset.attributes['color_image_list'],
                                                      self.dataset.attributes['thermal_image_list'])

        self.total = len(self.aligned_images)
        self.progress = 0
        if 'transformation_file' in self.dataset.attributes:
            os.environ['PIPE_ARG_TRANSFORMATION_FILE'] = self.dataset.attributes['transformation_file']
    def set_progress_iterator(self, iterator):
        self.progress_iterator = iterator


    def run(self):
        with stderr_redirected('stderr.txt'):
            with patch_stdout():
                pipe_runner = EmbeddedPipelineRunner(self.pipeline_fp)
                pipe_runner.load()
                pipe_runner.start()
                self.progress_iterator.start_time = datetime.datetime.now()
                for i in self.progress_iterator:
                    # print(self.progress)
                    if pipe_runner.full():
                        dets_eo, dets_ir = pipe_runner.receive()
                        for det in dets_eo:
                            index = det.index
                            bbox = det.bounding_box
                            confidence = det.confidence
                            classes = det.type.class_names()
                            x1 = bbox.min_x()
                            x2 = bbox.max_x()
                            y1 = bbox.min_y()
                            y2 = bbox.max_y()
                            # print('%d, (%d,%d  %d,%d) - %s - %.3f' % (index, int(x1), int(y1), int(x2), int(y2),
                            #                                           ','.join(classes), confidence))
                        for det in dets_ir:
                            index = det.index
                            bbox = det.bounding_box
                            confidence = det.confidence
                            classes = det.type.class_names()
                            x1 = bbox.min_x()
                            x2 = bbox.max_x()
                            y1 = bbox.min_y()
                            y2 = bbox.max_y()
                    #         print('%d, (%d,%d  %d,%d) - %s - %.3f' % (index, int(x1), int(y1), int(x2), int(y2),
                    #                                                   ','.join(classes), confidence))
                    # x = 1
                    eo_fp, ir_fp = self.aligned_images[self.progress]
                    if eo_fp is None or ir_fp is None:
                        self.progress += 1
                        # print('Skipped')
                        continue
                    t = datetime.datetime.now()
                    im_eo_kvr = load_image_kvr_container(eo_fp, ocv_load)
                    im_ir_kvr = load_image_kvr_container(ir_fp, ocv_load)
                    print(datetime.datetime.now()-t)
                    pipe_runner.send({'image_eo': im_eo_kvr, 'image_ir': im_ir_kvr})
                    self.progress += 1

                pipe_runner.ep.send_end_of_input()
                pipe_runner.stop()