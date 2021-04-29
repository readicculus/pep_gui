from src.util.image import load_image_kvr_container, ocv_load

try:
    import Queue
except ImportError:
    import queue as Queue
from threading import Event, Thread


class ImageThread(Thread):
    """Image Thread"""
    def __init__(self, queue: Queue, out_queue: Queue, stop_event: Event):
        Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            # Grabs list of tuples(rgb_path, ir_path) from queue
            path_pair_batch = self.queue.get()
            print('loading images')
            output = []
            for rgb_path, ir_path in path_pair_batch:
                im_eo_kvr = load_image_kvr_container(rgb_path, ocv_load)
                im_ir_kvr = load_image_kvr_container(ir_path, ocv_load)
                output.append((im_eo_kvr, im_ir_kvr))
            print('loaded images')
            # Place image in out queue
            self.out_queue.put(output)
            # Signals to queue job is done
            self.queue.task_done()

class ImageLoader:
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

    def run(self, data, processing_fn):
        batches = self.batch(data)
        data_len = len(data) / self.batch_size
        if self.__debug: print('%d batches' % data_len)

        stop_event = Event()
        for i in range(self.n_workers):
            t = ImageThread(self.queue, self.out_queue, stop_event)
            t.setDaemon(True)
            t.start()

        batch_iter = iter(batches)

        for i in range(self.input_size):
            batch = next(batch_iter, None)
            self.queue.put(batch)

        num_received = 0
        while True:
            data = self.out_queue.get()
            num_received += 1

            # process the data
            for d in data:
                processing_fn(d)

            if self.__debug: print('received %d batches' % num_received)
            if num_received == data_len:
                # complete
                stop_event.set()
                return

            # add to input queue so qsize is the expected input size
            qsize = self.queue.qsize()
            if  qsize <= self.input_size:
                for image_path_group in range(self.input_size-qsize):
                    batch = next(batch_iter, None)
                    if batch is None:
                        break # no more input data
                    self.queue.put(batch)
                    if self.__debug: print('added to input')







