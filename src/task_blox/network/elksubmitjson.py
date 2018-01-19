from task_blox.base import BaseTask
import socket
import json
import traceback
import logging


class ElkSubmitJson(BaseTask):
    KEY = 'ElkSubmitJson'

    def __init__(self, host, port, poll_time=60, name=None,
                 log_level=logging.INFO, logger_name=KEY.lower()):
        super(ElkSubmitJson, self).__init__(name, poll_time,
                                            log_level, logger_name)

        self.host = host
        self.port = port
        self.proc = None

    def get_args(self):
        return [
            self.poll_time,
            self.in_queue,
            self.out_queue,
            self.host,
            self.port,
        ]

    def add_json_data(self, tid, json_data):
        self.insert_inqueue({'json_data': json_data, 'tid': tid})
        return True

    def add_json_datas(self, tid, json_datas):
        for jd in json_datas:
            self.add_json_data(tid, jd)
        return True

    def add_json_msg(self, json_msg):
        if 'json_data' in json_msg or \
           'json_datas' in json_msg:
            self.insert_inqueue(json_msg)
            return True
        return False

    @classmethod
    def send_udp_json_line(cls, host, port, json_data):
        json_data_str = json.dumps(json_data)
        data = bytes(((json_data_str + '\n')).encode('utf-8'))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (host, port))

    @classmethod
    def send_udp_json_lines(cls, host, port, json_datas, tid=None):
        results = []
        for json_data in json_datas:
            status = 'error: unknown'
            try:
                json_data_str = json.dumps(json_data)
                data = bytes(((json_data_str + '\n')).encode('utf-8'))
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(data, (host, port))
                status = 'success'
            except:
                status = 'error: ' + traceback.format_exc()

            results.append({'tid': tid, 'status': status})
        return results

    @classmethod
    def handle_message(cls, json_msg, host, port, **kargs):
        tid = json_msg.get('tid', None)
        json_datas = json_msg.get('json_datas', [])
        json_data = json_msg.get('json_data', None)
        if json_data is not None:
            json_datas.append(json_data)
        return cls.send_udp_json_lines(host, port, json_datas, tid)

    @classmethod
    def from_toml(cls, toml_dict):
        host = toml_dict.get('host', '')
        port = toml_dict.get('port', 5002)
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        log_level = toml_dict.get('log-level', logging.INFO)
        logger_name = toml_dict.get('logger-name', cls.key())
        return cls(host, port, poll_time=poll_time, name=name,
                   log_level=log_level, logger_name=logger_name)
