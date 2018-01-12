import time
from multiprocessing import Queue, Process
import json
import mimetypes
import gzip

class ReadJsonFile(object):
    KEY = 'ReadJsonFile'

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    def __init__(self, poll_time=60, name=None):
        self.cmd_queue = Queue()
        self.out_queue = Queue()

        self.name = name
        self.poll_time = poll_time
        self.proc = None

    def read_outqueue(self):
        data = []
        while not self.out_queue.empty():
            data.append(self.out_queue.get())
        return data

    def start(self):
        args = [
            self.poll_time,
            self.cmd_queue,
            self.out_queue
        ]
        self.proc = Process(target=self.read_json_file, args=args)
        self.proc.start()

    def is_running(self):
        if self.proc is None or not self.proc.is_alive():
            return False
        return True

    def set_queues(self, cmd_queue, out_queue):
        if not self.is_running():
            self.cmd_queue = cmd_queue
            self.out_queue = out_queue

    def add_filename(self, filename):
        self.cmd_queue.put({'filename': filename})

    def stop(self):
        self.cmd_queue.put({'quit': True})
        time.sleep(2*self.poll_time)
        if self.proc.is_alive():
            self.proc.terminate()
        self.proc.join()

    @classmethod
    def read_inqueue(cls, queue):
        if queue.empty():
            return None
        return queue.get()

    @classmethod
    def check_for_quit(cls, json_data):
        quit = False
        if json_data is None:
            return quit

        if 'quit' in json_data:
            quit = True

        return quit

    @classmethod
    def open_file(cls, filename):
        ft = mimetypes.guess_type(filename)
        if ft[0] == 'application/json':
            return open(filename)
        elif ft[1] == 'gzip':
            return Gzip(filename)
        return None


    @classmethod
    def read_json_file(cls, poll_time, in_queue, out_queue):

        while True:
            d = cls.read_inqueue(in_queue)
            if cls.check_for_quit(d):
                break

            if 'filename' in d:
                filename = d.get('filename', None)
                json_lines = []
                infile = cls.open_file(filename)
                if infile is not None:
                    for line in infile.readlines():
                        try:
                            data = json.loads(line)
                            json_lines.append(data)
                            if len(json_lines) > 200:
                                out_queue.put({'json_lines': json_lines,
                                               'filename': filename,
                                               'status': 'incomplete'})
                                json_lines = []
                        except:
                            pass
                    infile.close()

                out_queue.put({'json_lines': json_lines,
                               'filename': filename,
                               'status': 'complete'})

            if in_queue.empty():
                time.sleep(poll_time)

    @classmethod
    def from_toml(cls, toml_dict):
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        return cls(poll_time=poll_time, name=name)
