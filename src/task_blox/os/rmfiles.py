from task_blox.base import BaseTask
from task_blox import logger
import os
import shutil
import traceback
import logging


class RmFiles(BaseTask):
    KEY = 'RmFiles'

    def __init__(self, poll_time=60, name=None,
                 log_level=logging.INFO, logger_name=KEY.lower()):
        super(RmFiles, self).__init__(name, poll_time,
                                      log_level, logger_name)

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
            logger.debug("Removed filename %s from the OS" % filename)
        except:
            logger.debug("Failed to remove filename %s from the OS" % filename)
            result['removed'] = False
            result['error'] = 'error: ' + traceback.format_exc()
        return result

    @classmethod
    def rm_directory(cls, filename, tid=None):
        result = {'directory': filename, 'error': '', 'tid': tid}
        try:
            shutil.rmtree(filename)
            result['removed'] = True
            logger.debug("Removed dir. %s from the OS" % filename)
        except:
            logger.debug("Failed to remove dir. %s from the OS" % filename)
            result['removed'] = False
            result['error'] = 'error: ' + traceback.format_exc()
        return result

    @classmethod
    def rm_file(cls, json_msg, tid=None):
        default = json_msg.copy()
        default['error'] = 'unknown filetype'
        default['removed'] = False

        if 'filename' in json_msg:
            return cls.rm_filename(json_msg['filename'], tid=tid)
        elif 'directory' in json_msg:
            return cls.rm_directory(json_msg['directory'], tid=tid)
        return default

    @classmethod
    def handle_message(cls, json_msg, *args, **kargs):
        tid = json_msg.get('tid', None)
        result = cls.rm_file(json_msg, tid=tid)
        return [result, ]

    @classmethod
    def post_process_log(cls, json_msg, results):
        line_cnt = 0
        for r in results:
            line_cnt += len(r.get('json_datas', []))

        filename = 'unknown'
        error = json_msg.get('error', '')
        status = json_msg.get('removed', False)

        if 'filename' in json_msg:
            filename = json_msg['filename']
        elif 'directory' in json_msg:
            filename = json_msg['directory']

        m = "%s removed (%s) %s: %s"
        logger.debug(m % (cls.key(), status, filename, error))

    @classmethod
    def from_toml(cls, toml_dict):
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        log_level = toml_dict.get('log-level', logging.INFO)
        logger_name = toml_dict.get('logger-name', cls.key())
        return cls(poll_time=poll_time, name=name,
                   log_level=log_level, logger_name=logger_name)
