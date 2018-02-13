from task_blox.base import BaseTask
from task_blox import logger
import socket
import json
import traceback
import logging
import psycopg2


class PGSubmitJsonNC(BaseTask):
    KEY = 'PGSubmitJsonNC'
    INSERT_STMT = "INSERT into {table} ({column}) VALUES ('{json_str}'::jsonb)"
    INSERT_MANY_STMT = "INSERT into {table} ({column}) VALUES ('{{json_str}}'::jsonb)"
    SELECT_STMT = "SELECT * from {table}"

    def __init__(self, host, port, database, table, column,
                 poll_time=60, name=None, username='postgres', password=None,
                 log_level=logging.INFO, logger_name=KEY.lower()):
        super(PGSubmitJsonNC, self).__init__(name, poll_time,
                                             log_level, logger_name)

        self.host = host
        self.port = port
        self.proc = None
        self.database = database
        self.table = table
        self.column = column
        self.username = username
        self.password = password

    def get_kwargs(self):
        return {
            "database": self.database,
            "table": self.table,
            "column": self.column,
            "username": self.username,
            "password": self.password,
        }

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
            logger.debug('adding message to elksubmitjson')
            self.insert_inqueue(json_msg)
            return True
        logger.debug('failed adding message to elksubmitjson')
        return False

    @classmethod
    def send_udp_json_line(cls, host, port, json_data):
        json_data_str = json.dumps(json_data)
        data = bytes(((json_data_str + '\n')).encode('utf-8'))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (host, port))

    @classmethod
    def connect_postgres(cls, host, port, database, username, password):
        try:
            conn = psycopg2.connect(host=host,
                                    port=port,
                                    dbname=database,
                                    user=username,
                                    password=password)
            return conn
        except:
            raise

    @classmethod
    def insert_json(cls, pg_conn, table, column, json_data):
        fmt_kargs = {'table': table,
                     'column': column,
                     'json_str': json.dumps(json_data)}
        stmt = cls.INSERT_STMT.format(**fmt_kargs)
        try:
            cur = pg_conn.cursor()
            cur.execute(stmt)
            return True
        except:
            raise

    @classmethod
    def postgress_insert_json(cls, host, port, database, table, column,
                              username, password, json_datas, tid=None):
        results = []
        pg_conn = cls.connect_postgres(host, port, database,
                                       username, password)
        for json_data in json_datas:
            status = 'error: connection failed'
            try:
                status = "error: failed to insert json into %s:%s"
                status = status % (table, column)
                r = cls.insert_json(pg_conn, table, column, json_data)
                if not r:
                    status = 'error: ' + traceback.format_exc()
                else:
                    status = 'success'
                logger.debug(cls.key() + ": %s:%s " % (host, port) + status)
                pg_conn.commit()
            except:
                status = 'error: ' + traceback.format_exc()
                logger.debug(cls.key() + ": %s:%s " % (host, port) + status)
                pg_conn.rollback()

            results.append({'tid': tid, 'status': status})
        try:
            pg_conn.close()
        except:
            pass
        return results

    @classmethod
    def handle_message(cls, json_msg, host, port, **kargs):
        database = kargs.get('database', None)
        table = kargs.get('table', None)
        column = kargs.get('column', None)
        username = kargs.get('username', None)
        password = kargs.get('password', None)
        tid = json_msg.get('tid', None)
        json_datas = json_msg.get('json_datas', [])
        json_data = json_msg.get('json_data', None)
        if json_data is not None:
            json_datas.append(json_data)
        return cls.postgress_insert_json(host, port, database, table,
                                         column, username, password,
                                         json_datas, tid)

    @classmethod
    def parse_toml(cls, toml_dict):
        host = toml_dict.get('host', '')
        port = toml_dict.get('port', 5432)
        poll_time = toml_dict.get('poll-time', 20)
        name = toml_dict.get('name', None)
        database = toml_dict.get('database', None)
        table = toml_dict.get('table', None)
        column = toml_dict.get('column', None)
        username = toml_dict.get('username', None)
        password = toml_dict.get('password', None)
        log_level = toml_dict.get('log-level', logging.INFO)
        logger_name = toml_dict.get('logger-name', cls.key())
        return cls(host, port, database, table, column,
                   poll_time=poll_time, name=name, log_level=log_level,
                   username=username, password=password,
                   logger_name=logger_name)
