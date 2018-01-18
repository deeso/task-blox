from task_blox.base import BaseTask
import traceback
import json
import time
from task_blox import logger
from manipin_json.enrichupsert import EnrichUpsertKeyedValue


class KeyedJsonUpdate(BaseTask):
    KEY = 'KeyedJsonUpdate'
    DEFAULT_VALUE_KEY = EnrichUpsertKeyedValue.DEFAULT_VALUE_KEY

    @classmethod
    def key(cls):
        return cls.KEY.lower()

    def __init__(self, poll_time=60, name=None, json_enrichers=[]):
        super(KeyedJsonUpdate, self).__init__(name, poll_time)
        self.json_enrichers = json_enrichers

    def get_kwargs(self):
        return {'json_enrichers': self.json_enrichers}

    def get_target(self):
        return self.enrich_json_values

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
        for json_data in json_datas:
            result = cls.perform_json_erichment(json_data, jes, tid=tid)
            results.append(result)
        return results

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
