from task_blox.base import BaseTask
from task_blox.support.filter import Filter
from task_blox import logger
import time
import os


class DirChecker(BaseTask):
    KEY = 'DirChecker'

    def __init__(self, target_dir, name_pattern=None, poll_time=30, name=None):
        super(DirChecker, self).__init__(name, poll_time)
        self.target_dir = target_dir
        self.name_pattern = name_pattern

    def get_kwargs(self):
        return {
            'target_dir': self.target_dir,
            'name_pattern': self.name_pattern,
            'files_found': set()}

    # def get_target(self):
    #     return self.check_dir

    @classmethod
    def is_fileopened(cls, fname):
        if not os.path.exists(fname):
            return None
        try:
            os.rename(fname, fname)
            return False
        except:
            return True
        return None

    @classmethod
    def identify_files(cls, target_directory, ffilter=None, files_found=set()):
        td = target_directory
        rfiles = [os.path.join(td, i) for i in os.listdir(td)]
        results = []

        for f in rfiles:

            if ffilter is None or ffilter.matches(f):
                if not cls.is_fileopened(f) and f not in files_found:
                    files_found.add(f)
                    z = {'other': f}
                    if os.path.isfile(f):
                        z = {'filename': f}
                    elif os.path.isfile(f):
                        z = {'directory': f}
                    results.append(z)
        return results, files_found

        def quick_check(name_dict):
            return name_dict.values()[0] if len(name_dict) == 1 else ''
        return sorted(results, key=quick_check), files_found

    @classmethod
    def handle_message(cls, json_msg, **kargs):
                    # target_dir=None,
                    # name_pattern=None, files_found=set()):
        logger.debug("%s Handling messages" % cls.key())
        target_dir = kargs.get('target_dir', None)
        name_pattern = kargs.get('name_pattern', None)
        files_found = kargs.get('files_found', set())
        ffilter = kargs.get('ffilter', None)
        results = []
        if target_dir is None:
            m = "Unable to scan invalid directory: %s"
            raise Exception(m % target_dir)

        ffilter = None
        if name_pattern is not None and ffilter is None:
            ffilter = Filter(name_pattern)
            kargs['ffilter'] = ffilter
            logger.debug("Setting the ffilter karg value")

        results, files_found = cls.identify_files(target_dir, ffilter,
                                                  files_found=files_found)
        kargs['files_found'] = files_found
        return results

    @classmethod
    def generic_task(cls, poll_time, in_queue, out_queue, *args, **kargs):
        logger.info("Entered the child thread: %s" % cls.key())
        while True:
            json_msg = cls.read_queue(in_queue)
            if json_msg is not None and cls.check_for_quit(json_msg):
                break

            # if json_msg is None:
            #     time.sleep(poll_time)
            #     continue

            results = cls.handle_message({}, *args, **kargs)
            cls.inserts_queue(out_queue, results)
            cls.post_process_log(json_msg, results)
            time.sleep(poll_time)

    @classmethod
    def from_toml(cls, toml_dict):
        target_directory = toml_dict.get('target-directory', None)
        name_pattern = toml_dict.get('name-pattern', None)
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        return cls(target_directory,
                   name_pattern=name_pattern,
                   poll_time=poll_time, name=name)
