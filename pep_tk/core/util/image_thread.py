from typing import Callable, List

from pep_tk.core.util.image import load_image_kvr_container, ocv_load

try:
    import Queue
except ImportError:
    import queue as Queue
from threading import Event, Thread

# single and dual-stream loading functions
def dual_stream_loading_fn(data):
    rgb_path, ir_path = data
    im_eo_kvr = load_image_kvr_container(rgb_path, ocv_load)
    im_ir_kvr = load_image_kvr_container(ir_path, ocv_load)
    return (im_eo_kvr, im_ir_kvr)

def single_stream_loading_fn(data):
    return load_image_kvr_container(data, ocv_load)


class ImageThread(Thread):
    """Image Thread for loading a batch of images """
    def __init__(self, queue: Queue, out_queue: Queue, stop_event: Event, image_loading_fn: Callable, debug = False):
        Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue
        self.stop_event = stop_event
        self.image_loading_fn = image_loading_fn
        self.__debug = debug

    def run(self):
        while not self.stop_event.is_set():
            # Grabs list of tuples(rgb_path, ir_path) from queue
            path_pair_batch = self.queue.get()
            if self.__debug: print('loading images')
            output = []
            for data in path_pair_batch:
                output.append(self.image_loading_fn(data))
            if self.__debug: print('loaded images')
            # Place image in out queue
            self.out_queue.put(output)
            # Signals to queue job is done
            self.queue.task_done()

class ImageLoader:
    ''' Threaded Image Loader '''
    def __init__(self, n_workers=4, input_size = 10, buffer_size=5, batch_size=5):
        self.queue = Queue.Queue()
        self.out_queue = Queue.Queue(maxsize=buffer_size)
        self.n_workers = n_workers
        self.input_size = input_size
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.__debug = False

    def batch(self, iterable):
        l = len(iterable)
        for ndx in range(0, l, self.batch_size):
            yield iterable[ndx:min(ndx + self.batch_size, l)]

    def run(self, data: List, processing_fn: Callable, image_loading_fn: Callable):
        '''
          :param data: list of image filenames or list of tuples of ir/eo filenames
          :param processing_fn: function for processing the output of image_loading_fn
          :param image_loading_fn: function to load one item from data
          :return:
          '''
        batches = self.batch(data)
        data_len = len(data) / self.batch_size
        if self.__debug: print('%d batches' % data_len)

        stop_event = Event()
        for i in range(self.n_workers):
            t = ImageThread(self.queue, self.out_queue, stop_event, image_loading_fn, debug=self.__debug)
            t.setDaemon(True)
            t.start()

        batch_iter = iter(batches)

        for i in range(self.input_size):
            batch = next(batch_iter, None)
            self.queue.put(batch)

        if self.__debug: print('ImageLoader: sent initial batches')

        num_received = 0
        while True:
            if not self.out_queue.empty():
                if self.__debug: print('ImageLoader: calling out_queue.get(), q size=%d'%self.out_queue.qsize())
                data = self.out_queue.get()
                num_received += 1
                if self.__debug: print('ImageLoader: received %d batches' % num_received)

                # process the data
                for item in data:
                    processing_fn(item)

                if self.__debug: print('ImageLoader: processed batch #%d' % num_received)

            if num_received == data_len:
                # complete
                if self.__debug: print('ImageLoader: stop_event was set')
                stop_event.set()
                return

            # add to input queue so qsize is the expected input size
            qsize = self.queue.qsize()
            if  qsize < self.input_size:
                for image_path_group in range(self.input_size - qsize):
                    if self.__debug: print('ImageLoader: adding to input, queue_size=%d'%self.queue.qsize())
                    batch = next(batch_iter, None)
                    if batch is None:
                        if self.__debug: print('ImageLoader: no more input found')
                        break # no more input data
                    self.queue.put(batch)
                    if self.__debug: print('ImageLoader: added to input, queue_size=%d'%self.queue.qsize())






