import os
import logging
import sys
from logging.handlers import RotatingFileHandler

loggers = {}
main_log_handler = None
console_log_handler = None
log_format = '[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s'
log_dir = 'logs'
log_file_name = 'env.log'

ENV_PQ_DEBUG_LEVEL = "PQ_DEBUG_LEVEL"



def attach_bot_log_handler(logger):
    # create main log handler
    global main_log_handler
    global console_log_handler

    # Create the file handler
    if main_log_handler is None:
        # Make sure the log directory exists
        log_file_path = log_dir + "/" + log_file_name
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        open(log_file_path, 'a').close()

        # Create the log handler
        log_handler = RotatingFileHandler(os.path.join(log_dir, log_file_name), maxBytes=10 * 1024 * 1024, backupCount=5)
        log_formatter = logging.Formatter(log_format)
        log_handler.setFormatter(log_formatter)

        log_levels = {
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
        }
        # get or default WARNING
        env_pq_debug = os.getenv(ENV_PQ_DEBUG_LEVEL)
        if env_pq_debug is None or env_pq_debug == "":
            env_pq_debug = logging.WARNING
        else:
            env_pq_debug = int(env_pq_debug)
        
        log_handler.setLevel(env_pq_debug)
        main_log_handler = log_handler

    # Create the console log handler
    if console_log_handler is None:
        log_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter(log_format)
        log_handler.setFormatter(log_formatter)
        log_handler.setLevel(env_pq_debug)
        console_log_handler = log_handler

    if logger is not None:
        logger.addHandler(main_log_handler)
        logger.addHandler(console_log_handler)


def get_logger(logger_name='default'):
    loggername = 'penquest.{}'.format(logger_name)

    if loggers.get(loggername):
        return loggers.get(loggername)

    logger = logging.getLogger(loggername)
    attach_bot_log_handler(logger)
    logger.setLevel(1)

    loggers[loggername] = logger
    return logger
