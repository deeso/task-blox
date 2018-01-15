import socket
import time
from multiprocessing import Queue, Process
import json


class ElkSubmitJson(object):
    KEY = 'ElkSubmitJson'

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    def __init__(self, host, port, poll_time=60, name=None):
        self.cmd_queue = Queue()
        self.out_queue = Queue()

        self.name = name
        self.poll_time = poll_time
        self.host = host
        self.port = port
        self.proc = None

    def read_outqueue(self):
        data = []
        while not self.out_queue.empty():
            data.append(self.out_queue.get())
        return data

    def start(self):
        args = [
            self.poll_time,
            self.host,
            self.port,
            self.cmd_queue,
            self.out_queue
        ]
        self.proc = Process(target=self.elk_submit_json, args=args)
        self.proc.start()

    def is_running(self):
        if self.proc is None or not self.proc.is_alive():
            return False
        return True

    def set_queues(self, cmd_queue, out_queue):
        if not self.is_running():
            self.cmd_queue = cmd_queue
            self.out_queue = out_queue

    def stop(self):
        self.cmd_queue.put({'quit': True})
        time.sleep(2*self.poll_time)
        if self.proc.is_alive():
            self.proc.terminate()
        self.proc.join()

    def add_json_string(self, tid, json_str):
        json_data = json.loads(json_str)
        self.cmd_queue.put({'json_data': json_data, 'tid': tid})

    def add_json_data(self, tid, json_data):
        self.cmd_queue.put({'json_data': json_data, 'tid': tid})

    def add_json_datas(self, tid, json_datas):
        self.cmd_queue.put({'json_datas': json_datas, 'tid': tid})

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
    def send_udp_json_line(cls, host, port, json_data):
        data = bytes(((json_data + '\n')).encode('utf-8'))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (host, port))

    @classmethod
    def send_udp_json_lines(cls, host, port, json_datas):
        for json_data in json_datas:
            data = bytes(((json_data + '\n')).encode('utf-8'))
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data, (host, port))

    @classmethod
    def elk_submit_json(cls, poll_time, host, port, in_queue, out_queue):

        while True:
            d = cls.read_inqueue(in_queue)

            if d is None:
                time.sleep(poll_time)
            elif cls.check_for_quit(d):
                break

            status = 'success'
            json_datas = d.get('json_datas', None)
            json_data = d.get('json_data', None)
            if json_data is not None:
                json_datas = [json_data, ]

            for json_data in json_datas:
                try:
                    cls.send_udp_json_line(host, port, json_data)
                except:
                    status = 'error'
                    break

            out_queue.put({'tid': d.get('tid', None),
                           'status': status})

            if in_queue.empty():
                time.sleep(poll_time)

    @classmethod
    def from_toml(cls, toml_dict):
        host = toml_dict.get('host', '')
        port = toml_dict.get('port', 5002)
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        return cls(host, port, poll_time=poll_time, name=name)
