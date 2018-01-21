from task_blox import logger
from task_blox.base import BaseTask
import os
import traceback
import json
import mimetypes
from gzip import GzipFile
import logging


class ReadJsonFile(BaseTask):
    KEY = 'ReadJsonFile'

    def __init__(self, poll_time=60, name=None,
                 log_level=logging.INFO, logger_name=KEY.lower()):
        super(ReadJsonFile, self).__init__(name, poll_time,
                                           log_level, logger_name)

    def add_filename(self, filename, tid=None):
        self.insert_inqueue({'filename': filename, 'tid': tid})

    def add_filenames(self, filenames, tid=None):
        for filename in filenames:
            self.add_filename(filename, tid)

    def add_json_msg(self, json_msg):
        if 'filename' in json_msg or \
           'directory' in json_msg:
            self.insert_inqueue(json_msg)
            return True
        return False

    @classmethod
    def open_file(cls, filename):
        ft = mimetypes.guess_type(filename)
        if ft[0] == 'application/json':
            return open(filename)
        elif ft[1] == 'gzip':
            return GzipFile(filename)
        return None

    @classmethod
    def ingest_file(cls, filename, tid=None):
        json_datas = []
        status = 'failed'
        infile = cls.open_file(filename)
        results = []
        if infile is not None:

            lines = infile.readlines()
            infile.close()
            try:
                json_datas = [json.loads(_line.strip()) for _line in lines]
                status = 'success'
            except:
                status = 'error: ' + traceback.format_exc()

        for jd in json_datas:
            result = {'filename': filename,
                      'tid': tid,
                      'json_data': jd,
                      'status': status,
                      'completed': False,
                      'allowed_to_manip': False}
            results.append(result)

        results[-1]['completed'] = True
        results[-1]['allowed_to_manip'] = True
        return results

    @classmethod
    def ingest_dir(cls, filename, tid=None):
        filenames = [os.path.join(filename, i) for i in os.listdir(filename)]
        results = []
        for i in filenames:
            results = results + cls.ingest_file(i, tid)
        result = {'directory': filename,
                  'tid': tid,
                  'json_datas': None,
                  'status': 'success'}
        results.append(result)
        return results

    @classmethod
    def handle_message(cls, json_msg, *args, **kargs):
        results = []
        filename = 'unknown'
        tid = json_msg.get('tid', None)
        if 'filename' in json_msg:
            filename = json_msg.get('filename', None)
            results = cls.ingest_file(filename, tid=tid)
        elif 'directory' in json_msg:
            filename = json_msg.get('directory', None)
            results = cls.ingest_dir(filename, tid=tid)
        else:
            results = [{'other': str(json_msg), 'tid': tid,
                        'json_datas': [],
                        'status': 'failed unknown type'}]
        return results

    @classmethod
    def post_process_log(cls, json_msg, results):
        line_cnt = 0
        for r in results:
            if 'json_data' in r:
                line_cnt += 1

        filename = 'unknown'
        if 'filename' in json_msg:
            filename = json_msg['filename']
        elif 'directory' in json_msg:
            filename = json_msg['directory']

        m = "%s processed %s lines from %s"
        logger.debug(m % (cls.key(), line_cnt, filename))

    @classmethod
    def parse_toml(cls, toml_dict):
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        log_level = toml_dict.get('log-level', logging.INFO)
        logger_name = toml_dict.get('logger-name', cls.key())
        return cls(poll_time=poll_time, name=name,
                   log_level=log_level, logger_name=logger_name)
