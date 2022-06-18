import logging
import os
from psycopg2 import connect, extras
from contextlib import contextmanager
from configparser import ConfigParser
from fuzzywuzzy import fuzz
import re
#from postgres_dbconnect import insert_dict_to_table, get_results_as_dframe



BOT_TABLE_NAME = 'digit_bots.t_logger_info'
ERROR_CODE_TABLE = 'digit_bots.t_error_code_master'



err_query = f"""SELECT error_code, exception FROM {ERROR_CODE_TABLE} order by id desc"""
# parser = ConfigParser()
# section = 'nonabs_digit'
# parser.read('config.ini')
#
# if parser.has_section(section):
#     params = dict(parser.items(section))
# else:
#     raise Exception('Section {0} not found in the {1} file'.format(section, 'config.ini'))


# @contextmanager
# def get_cursor():
#     """create database cursor"""
#     conn = connect(**params)
#     try:
#         yield conn.cursor()
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         raise e
#     finally:
#         conn.close()
#
#
# with get_cursor() as cur:
#     cur.execute(err_query)
#     result_set = cur.fetchall()


def preprocessing(data):
    """It will clean string if unnecessary characters are present"""
    # if str(data).startswith('[') and str(data).endswith(']'):
    #     data = data.strip('[]')
    # data = re.sub(r'\[(?:[^\]|]*\|)?([^\]|]*)\]', "", str(data))
    data = re.sub(r'([0-9]{4}-[0-9]*-[0-9]* [0-9]*:[0-9]{2}.[0-9]{2}:[0-9]{3})', "", str(data))

    #return str(data).strip(" {}()[]':,\/")
    return str(data)

# ERROR_CODE_DICT = {'a': {
#     501: "ABCD",
#     502: "ACDS"
# }}
# result_set = ((500,"AWQER"),(500,"TWQER"))

result_set = get_results_as_dframe(err_query, "pre_bot_oem", "preprod_oem")

result_set = result_set.values.tolist()

#Createing error_code dict
ERROR_CODE_DICT = {}
for i in result_set:
    if preprocessing(i[1])[0].lower() in ERROR_CODE_DICT.keys():
        ERROR_CODE_DICT[preprocessing(i[1])[0].lower()].update({i[0]: preprocessing(i[1])})
    else:
        ERROR_CODE_DICT[i[1][0].lower()] = {i[0]: preprocessing(i[1])}


class TailLogHandler(logging.Handler):
    """It will convert log into string """
    def init(self, log_queue):
        logging.Handler.init(self)
        self.log_queue = log_queue

    def emit(self, record):
        """string log into a list as a string"""
        self.log_queue.clear()
        self.log_queue.append(self.format(record))
        self.log_queue.append(record.getMessage())


class TailLogger(object):
    def init(self):
        self._log_queue = []
        self._log_handler = TailLogHandler(self._log_queue)

    def contents(self):
        """It will return the log"""
        return self._log_queue

    @property
    def log_handler(self):
        return self._log_handler


def fuzzywuzzy_logic(error_msg, matching_error):
    """It will give the matching pattern score of two strings and return the height matching details else None"""
    score = {key:fuzz.partial_ratio(error_msg, matching_error[key]) for key in matching_error}
    print(score)
    max_score_key = max(zip(score.values(), score.keys()))[1]
    print(max_score_key)
    if score[max_score_key] >= 65:
        return max_score_key
    return

def get_error_code(error_msg):
    """It will fetch the error code if it will available in database esle it will return None"""
    matching_errors = ERROR_CODE_DICT[error_msg.strip()[0].lower()]
    error_status_code = None
    for error_code, err_desc in matching_errors.items():
        if preprocessing(error_msg.lower()) == preprocessing(err_desc.lower()) or \
                preprocessing(err_desc.lower()) .contains(preprocessing(error_msg.lower())) or \
                preprocessing(error_msg.lower()).contains(preprocessing(err_desc.lower())):
            error_status_code = error_code
            break
    if not error_status_code:
        error_status_code = fuzzywuzzy_logic(error_msg, matching_errors)
    return error_status_code

def recordLogDB( bot_id=None, id_num=None, app_name=None, log_string=None, query_runner=None):
    """will insert log into database
    db_columns = ['bot_id', 'transaction_number', 'application_name', 'insertion_time', 'logger_type', 'file_name',
              'function_name', 'line_number', 'logger_msg']
    """
    db_columns = ['bot_id', 'transaction_number', 'application_name', 'insertion_time', 'logger_type', 'file_name',
                  'function_name', 'line_number', 'logger_msg']
    values = [bot_id, id_num, app_name]+log_string[0].split(' - ')
    data = {}
    for i in range(len(db_columns)):
        if type(i) == str:
            data.setdefault(db_columns[i], values[i].strip())
        else:
            data.setdefault(db_columns[i], values[i])

    data.update({'insertion_time': data['insertion_time'].replace(",", '.')})
    data.update({'logger_msg': data['logger_msg'].replace("'", '"')})
    #print(data)

    if data['logger_type'].lower() == 'error':
        error_code = get_error_code(log_string[-1])
        if not error_code:
            error_code = 9040
            db_columns.append("error_code")
            data.update({'error_code': error_code})
        else:
            db_columns.append("error_code")
            data.update({'error_code': error_code})

    print(data)
    #insert_dict_to_table(BOT_TABLE_NAME, data, "pre_bot_oem", "preprod_oem")

    # # sql = f"""INSERT INTO {BOT_TABLE_NAME} ("{'","'.join(db_columns)}") VALUES {tuple(data.values())};"""
    # # print(sql)
    # # insert_dataframe_to_table(table_name, dframe, user_name, env, ignore_conflict=False)
    # # with get_cursor() as cur:
    # #     cur.execute(sql)


class LoggerLib:
    def init(self, level="INFO"):
        #self.Current_path = Current_path
        self.level = level

    def set_level(self, handler):
        """setting the level"""
        if self.level.lower() == "info":
            return handler.setLevel(logging.INFO)
        elif self.level.lower() == "debug":
            return handler.setLevel(logging.DEBUG)
        elif self.level.lower() == "warning":
            return handler.setLevel(logging.WARNING)
        elif self.level.lower() == "error":
            return handler.setLevel(logging.ERROR)
        elif self.level.lower() == "critical":
            return handler.setLevel(logging.CRITICAL)

    def set_logger(self, name='logger'):
        """configuring the logger and returning"""
        logger = logging.getLogger(name)

        # BASE_DIR = os.path.abspath(self.Current_path)
        # LOGS_DIR = os.path.join(BASE_DIR, "Logs")
        # os.makedirs(LOGS_DIR, exist_ok=True)

        LOG_FORMATTER = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')
        tail = TailLogger()
        self.set_level(logger)

        # FILE_HANDLER = RotatingFileHandler(os.path.join(LOGS_DIR, f'{name}.log'), 'a',
        #                        maxBytes=10000000, backupCount=10)
        # FILE_HANDLER.setFormatter(LOG_FORMATTER)
        # self.set_level(FILE_HANDLER)
        # logger.addHandler(FILE_HANDLER)
        #
        # CONSOLE_HANDLER = logging.StreamHandler()
        # CONSOLE_HANDLER.setFormatter(LOG_FORMATTER)
        # self.set_level(CONSOLE_HANDLER)
        # logger.addHandler(CONSOLE_HANDLER)

        Log_Handler = tail.log_handler
        Log_Handler.setFormatter(LOG_FORMATTER)
        logger.addHandler(Log_Handler)

        return logger, tail