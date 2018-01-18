from task_blox.base import BaseTask
from task_blox import logger
import os
import shutil
import traceback


class RmFiles(BaseTask):
    KEY = 'RmFiles'

    def __init__(self, poll_time=60, name=None):
        super(RmFiles, self).__init__(name, poll_time)

    def add_filename(self, tid, filename):
        r = {}
        if not os.path.isdir(filename):
            r = {'filename': filename, 'tid': tid}
        else:
            r = {'directory': filename, 'tid': tid}
        if len(r) > 0:
            self.insert_inqueue(r)
            return True
        return False

    def add_directory(self, tid, filename):
        self.add_filename(tid, filename)

    def add_json_msg(self, json_msg):
        if 'filename' in json_msg or \
           'directory' in json_msg:
            self.insert_inqueue(json_msg)
            return True
        return False

    @classmethod
    def rm_filename(cls, filename, tid=None):
        result = {'filename': filename, 'error': '', 'tid': tid}
        try:
            os.remove(filename)
            result['removed'] = True
        except:
            result['removed'] = False
            result['error'] = 'error: ' + traceback.format_exc()
        return result

    @classmethod
    def rm_directory(cls, filename, tid=None):
        result = {'directory': filename, 'error': '', 'tid': tid}
        try:
            shutil.rmtree(filename)
            result['removed'] = True
        except:
            result['removed'] = False
            result['error'] = 'error: ' + traceback.format_exc()
        return result

    @classmethod
    def rm_file(cls, label, name, tid=None):
        default = {label: name,
                   'error': 'unknown filetype',
                   'removed': False}

        if label == 'filename':
            return cls.rm_filename(name, tid=tid)
        elif label == 'directory':
            return cls.rm_directory(name, tid=tid)
        return default

    @classmethod
    def handle_message(cls, json_msg, *args, **kargs):
        tid = json_msg.get('tid', None)
        label = 'unknown'
        name = None
        if 'filename' in json_msg:
            name = json_msg.get('filename', None)
        elif 'directory' in json_msg:
            name = json_msg.get('directory', None)
        else:
            name = str(json_msg)

        result = cls.rm_file(label, name, tid=tid)
        return [result, ]

    @classmethod
    def post_process_log(cls, json_msg, results):
        line_cnt = 0
        for r in results:
            line_cnt += len(r.get('json_datas', []))

        filename = 'unknown'
        if 'filename' in json_msg:
            filename = json_msg['filename']
        elif 'directory' in json_msg:
            filename = json_msg['directory']

        m = "%s removed %s"
        logger.debug(m % (cls.key(), filename))

    @classmethod
    def from_toml(cls, toml_dict):
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        return cls(poll_time=poll_time, name=name)
