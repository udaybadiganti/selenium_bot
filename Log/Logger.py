import collections
import logging
from logging.handlers import RotatingFileHandler
import psycopg2
from psycopg2 import connect, extras
from configparser import ConfigParser
import os
from fuzzywuzzy import fuzz
import sys
sys.tracebacklimit = 0
from fuzzywuzzy import process

parser = ConfigParser()
section = 'digit'
parser.read('config.ini')

if parser.has_section(section):
    parms = dict(parser.items(section))
else:
    raise Exception("section not found")
    
col = ["bot_id", "id_num", "app_name", "insert_time", "logger_type",  "file_name", "func_name", "line_num", "logger_msg"]

conn = connect(**parms)
curr = conn.cursor()
logger = logging.getLogger()

error_sql = f"""select error_dode, description from uday.error_code"""

curr.execute(error_sql)
result_set = curr.fetchall()
error_dict = {i[0]: i[1] for i in result_set}
print(error_dict)

class TailLogHandler(logging.Handler):

    def __init__(self, log_queue):
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.clear()
        self.log_queue.append(self.format(record))
        print(record.getMessage())
        #print(str(record).split(',')[-1].strip(' ">'))
        self.log_queue.append(record.getMessage())

class TailLogger(object):

    def __init__(self):
        self._log_queue = []
        self._log_handler = TailLogHandler(self._log_queue)

    def contents(self):
        return self._log_queue

    @property
    def log_handler(self):
        return self._log_handler

def recordDbLog(bot_id = None, id_num = None, app_name = None, log_string = None):
    values = []
    flag = 0
    values.append(bot_id)
    values.append(id_num)
    values.append(app_name)
    string = log_string[0].split(' - ')
    for i in string:
        values.append(i.strip())
    values[3] = values[3].replace(',', '.')
    values[-1] =  log_string[-1]
    if values[4].lower() == 'error':
        values[-1] = values[-1].replace("'", '"')
        text_score = []
        for key in error_dict:
            if fuzz.ratio(error_dict[key], values[-1]) >= 90 :
                break
            else:
                text_score.append(fuzz.ratio(error_dict[key], values[-1]))
            if error_dict[key] == values[-1]:
                flag = 1
                values.append(key)
                col.append("error_code")
                sql = f"""INSERT INTO uday.bots ("{'","'.join(col)}") VALUES {tuple(values)};"""
                curr.execute(sql)
                conn.commit()
        if flag == 0:
            sql = f"""INSERT INTO uday.bots ("{'","'.join(col)}") VALUES {tuple(values)};"""
            curr.execute(sql)
            conn.commit()

    else:
        sql = f"""INSERT INTO uday.bots ("{'","'.join(col)}") VALUES {tuple(values)};"""
        curr.execute(sql)
        conn.commit()

class LoggerLib():
    def __init__(self, Current_Path= None, level = "INFO"):
        self.Current_path = Current_Path
        self.level = level
    
    def set_level(self, handler):
        if self.level.lower() == "info":
            return handler.setLevel(logging.INFO)
        elif self.level.lower() == "debug":
            return handler.setLevel(logging.DEBUG)

    def set_Logger(self):
        BASE_DIR = os.path.abspath(self.Current_path)
        LOGG_DIR = os.path.join(BASE_DIR, "Logs")
        os.makedirs(LOGG_DIR, exist_ok=True)
        LOG_FORMATTER = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')
        #logger = logging.getLogger()
        tail = TailLogger()
        self.set_level(logger)
        
        File_handler = RotatingFileHandler(os.path.join(LOGG_DIR, 'log.log'), mode = 'a', maxBytes=100000000, backupCount=10)
        File_handler.setFormatter(LOG_FORMATTER)
        self.set_level(File_handler)
        logger.addHandler(File_handler)

        # Console_handler = logging.StreamHandler()
        # self.set_level(Console_handler)
        # Console_handler.setFormatter(LOG_FORMATTER)
        # logger.addHandler(Console_handler)

        log_handler = tail.log_handler
        log_handler.setFormatter(LOG_FORMATTER)
        logger.addHandler(log_handler)
        
        return logger, tail