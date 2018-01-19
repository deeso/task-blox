from threading import Thread
from task_blox import logger
import toml
import json
import time
from multiprocessing import Process, Queue
import logging


class BaseTask(object):
    KEY = 'BaseTask'

    def __init__(self, name, poll_time,
                 log_level=logging.INFO, logger_name='task-blox'):
        logger.init_logger(name=logger_name, log_level=log_level)
        self.in_queue = Queue()
        self.out_queue = Queue()

        self.name = name
        self.poll_time = poll_time
        self.proc = None
        self.keep_running = False
        self.death_thread = None

    def get_kwargs(self):
        return {}

    def get_args(self):
        return [
            self.poll_time,
            self.in_queue,
            self.out_queue
        ]

    def get_target(self):
        return self.generic_task

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    def add_json_msg(self, json_msg):
        return False

    def set_queues(self, in_queue, out_queue):
        if not self.is_running():
            self.in_queue = in_queue
            self.out_queue = out_queue

    def read_outqueue(self):
        return self.read_queue(self.out_queue)

    def read_all_outqueue(self):
        return self.read_all_queue(self.out_queue)

    def read_inqueue(self):
        return self.read_queue(self.in_queue)

    def read_all_inqueue(self):
        return self.read_all_queue(self.in_queue)

    def has_msgs_inqueue(self):
        return not self.in_queue.empty()

    def has_msgs_outqueue(self):
        return not self.out_queue.empty()

    @classmethod
    def inserts_queue(cls, queue, data_dicts):
        for data_dict in data_dicts:
            cls.insert_queue(queue, data_dict)

    @classmethod
    def insert_queue(cls, queue, data_dict):
        o = json.dumps(data_dict)
        queue.put(o)

    def insert_out_queue(self, data_dict):
        self.inserts_queue(self.out_queue, [data_dict, ])

    def insert_inqueue(self, data_dict):
        self.inserts_queue(self.in_queue, [data_dict, ])

    def inserts_out_queue(self, data_dicts):
        self.inserts_queue(self.out_queue, data_dicts)

    def inserts_inqueue(self, data_dicts):
        self.inserts_queue(self.in_queue, data_dicts)

    @classmethod
    def read_queue(cls, queue):
        if queue.empty():
            return None
        d = queue.get()
        try:
            return json.loads(d)
        except:
            pass

        if isinstance(d, dict):
            return d
        else:
            return {'data': d}

    @classmethod
    def read_all_queue(cls, queue):
        data = []
        while not queue.empty():
            d = cls.read_queue(queue)
            data.append(d)
        return data

    def start(self):
        logger.info("Starting %s" % self.key())
        self.keep_running = True
        args = self.get_args()
        kargs = self.get_kwargs()
        target = self.get_target()
        self.proc = Process(target=target, args=args, kwargs=kargs)
        self.proc.start()
        logger.info("Starting %s completed" % self.key())

    def timed_thread_death(self):
        time.sleep(2*self.poll_time)
        if self.proc.is_alive():
            self.proc.terminate()
        self.proc.join()
        logger.info("Stopping %s completed" % self.key())

    def stop(self):
        logger.info("Stopping %s" % self.key())
        self.keep_running = False
        self.in_queue.put({'quit': True})
        self.death_thread = Thread(target=self.timed_thread_death)
        self.death_thread.start()

    @classmethod
    def handle_message(cls, json_msg, *args, **kargs):
        raise Exception("Implementation needed")

    @classmethod
    def post_process_log(cls, json_msg, results):
        pass

    @classmethod
    def generic_task(cls, poll_time, in_queue, out_queue, *args, **kargs):
        logger.info("Entered the child thread: %s" % cls.key())
        while True:
            json_msg = cls.read_queue(in_queue)
            if json_msg is not None and cls.check_for_quit(json_msg):
                break

            if json_msg is None:
                time.sleep(poll_time)
                continue

            results = cls.handle_message(json_msg, *args, **kargs)
            cls.inserts_queue(out_queue, results)
            cls.post_process_log(json_msg, results)

    @classmethod
    def check_for_quit(cls, json_data):
        quit = False
        if json_data is None:
            return quit
        if 'quit' in json_data:
            quit = True
        return quit

    def is_running(self):
        if self.proc is None or not self.proc.is_alive():
            return False
        return True

    @classmethod
    def from_toml(cls, toml_dict):
        return cls('basetask default', 100000000)

    @classmethod
    def from_toml_file(cls, filename):
        return cls(toml.load(open(filename)))
