import traceback
import json
import time
from multiprocessing import Queue, Process
from task_blox import logger
from manipin_json.enrichupsert import EnrichUpsertKeyedValue


class KeyedJsonUpdate(object):
    KEY = 'ReadJsonFile'
    DEFAULT_VALUE_KEY = EnrichUpsertKeyedValue.DEFAULT_VALUE_KEY

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    def __init__(self, poll_time=60, name=None, json_enrichers=[]):
        self.cmd_queue = Queue()
        self.out_queue = Queue()

        self.name = name
        self.poll_time = poll_time
        self.proc = None
        self.json_enrichers = json_enrichers

    def read_outqueue(self):
        data = []
        while not self.out_queue.empty():
            data.append(self.out_queue.get())
        return data

    def start(self):
        logger.info("Starting %s" % self.key())
        args = [
            self.poll_time,
            self.cmd_queue,
            self.out_queue,
            self.json_enrichers
        ]
        self.proc = Process(target=self.enrich_json_values, args=args)
        self.proc.start()

    def is_running(self):
        if self.proc is None or not self.proc.is_alive():
            return False
        return True

    def set_queues(self, cmd_queue, out_queue):
        if not self.is_running():
            self.cmd_queue = cmd_queue
            self.out_queue = out_queue

    def add_json_string(self, tid, json_str):
        json_data = json.loads(json_str)
        self.cmd_queue.put({'json_data': json_data, 'tid': tid})

    def add_json_data(self, tid, json_data):
        self.cmd_queue.put({'json_data': json_data, 'tid': tid})

    def add_json_datas(self, tid, json_datas):
        self.cmd_queue.put({'json_datas': json_datas, 'tid': tid})

    def add_filename(self, filename):
        self.cmd_queue.put({'filename': filename})

    def stop(self):
        logger.info("Stopping %s" % self.key())
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
    def perform_json_erichment(cls, json_data, json_enrichers):
        results = {}
        for je in json_enrichers:
            r = je.enrich_set(json_data)
            results[je.name] = r
        return results, json_data

    @classmethod
    def enrich_json_values(cls, poll_time, in_queue, out_queue,
                           json_enrichers):
        logger.info("Entered the child thread: %s" % cls.key())
        while True:
            d = cls.read_inqueue(in_queue)
            if d is not None and cls.check_for_quit(d):
                break

            if d is None:
                time.sleep(poll_time)
                continue
            # TODO read json lines run each line
            # through the enrichment process
            # return the json to the output queue
            status = 'success'
            json_datas = d.get('json_datas', [])
            json_data = d.get('json_data', None)
            if json_data is not None:
                json_datas = json_datas + [json_data, ]

            for json_data in json_datas:
                results = {}
                status = ""
                try:
                    results = cls.json_enrichers(json_data, json_enrichers)
                except:
                    status = 'error: ' + traceback.format_exc()

                out_queue.put({'tid': d.get('tid', None), 'status': status,
                              'json_data': json_data, 'results': results})

            if in_queue.empty():
                time.sleep(poll_time)

    @classmethod
    def from_toml(cls, toml_dict):
        # TODO update parsing process here
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)

        enrichers_blocks = toml_dict.get('json-enrichers', {})
        json_enrichers = []
        for name, block in enrichers_blocks.items():
            dpath_check = block.get('dpath-check', None)
            dpath_upsert = block.get('dpath-upsert', None)
            dpath_extract_key = block.get('dpath-extract-key', None)
            value_dict = block.get('value-dict')
            dk = cls.DEFAULT_VALUE_KEY
            default_value_key = block.get('default-value-key', dk)
            je = EnrichUpsertKeyedValue(dpath_check, dpath_upsert,
                                        dpath_extract_key, value_dict,
                                        default_value_key)
            json_enrichers.append(je)

        return cls(poll_time=poll_time, name=name)
