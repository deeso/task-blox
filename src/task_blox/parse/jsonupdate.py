from manipin_json.upsertwithvaluedict import UpsertWithKeyedValueDict
from task_blox.logger import logger
from task_blox.base import BaseTask
import traceback
import logging


class KeyedJsonUpdate(BaseTask):
    KEY = 'KeyedJsonUpdate'
    DEFAULT_VALUE_KEY = UpsertWithKeyedValueDict.DEFAULT_VALUE_KEY

    def __init__(self, poll_time=60, name=None, json_enrichers=[],
                 log_level=logging.DEBUG, logger_name=KEY.lower()):
        super(KeyedJsonUpdate, self).__init__(name, poll_time,
                                              log_level=log_level,
                                              logger_name=logger_name)
        self.json_enrichers = json_enrichers

    def get_kwargs(self):
        return {'json_enrichers': self.json_enrichers}

    def add_json_data(self, tid, json_data):
        self.insert_inqueue({'json_data': json_data, 'tid': tid})

    def add_json_datas(self, tid, json_datas):
        for jd in json_datas:
            self.add_json_data(tid, jd)

    @classmethod
    def perform_json_erichment(cls, json_data, json_enrichers, tid=None):
        results = {}
        for je in json_enrichers:
            status = 'success'
            try:
                r = je.enrich_set(json_data)
            except:
                status = 'error: ' + traceback.format_exc()

            results[je.name] = {'result': r, 'status': status}
        return {'results': results, 'status': status,
                'json_data': json_data, 'tid': tid}

    @classmethod
    def handle_message(cls, json_msg, *args, **kargs):
        tid = json_msg.get('tid', None)
        jes = kargs.get('json_enrichers', [])

        json_datas = json_msg.get('json_datas', [])
        json_data = json_msg.get('json_data', None)
        if json_data is not None:
            json_datas = json_datas + [json_data, ]

        results = []
        m = "performing enrichment on %d records" % len(json_datas)
        logger.debug(m)
        for json_data in json_datas:
            result = cls.perform_json_erichment(json_data, jes, tid=tid)
            print (json_data)
            results.append(result)
        print (results)
        return results

    @classmethod
    def parse_toml(cls, in_toml_dict):
        # TODO update parsing process here
        toml_dict = in_toml_dict[cls.key()] if cls.key() in in_toml_dict \
                                            else in_toml_dict
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)

        log_level = toml_dict.get('log-level', logging.INFO)
        logger_name = toml_dict.get('logger-name', cls.key())

        enrichers_blocks = toml_dict.get('json-enrichers', {})
        json_enrichers = []
        for name, block in enrichers_blocks.items():
            je = UpsertWithKeyedValueDict.parse_toml(block)
            json_enrichers.append(je)

        return cls(poll_time=poll_time, name=name,
                   log_level=log_level, logger_name=logger_name,
                   json_enrichers=json_enrichers)
