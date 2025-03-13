import os
import logging
import sys
from logging.handlers import RotatingFileHandler

main_log_handler = None
console_log_handler = None
log_format = '[%(asctime)s][%(class_name)-46s][%(game)s][%(connection_id)s][%(role)s][%(taskName)s][%(levelname)s]-%(message)s'
log_dir = 'logs'
log_file_name = 'env.log'

LOG_LEVEL_NETWORK_MINOR = 4
LOG_LEVEL_NETWORK = 5

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


def get_logger(
        class_name: str='default', 
        connection_id: str=None, 
        game: str='None',
        role: str='None',
    ) -> logging.Logger:

    extra = {
        'class_name': class_name,
        'game': game,
        'connection_id': connection_id if connection_id is not None else 'None',
        'role': role,
    }

    # create a specific default logger with a name, otherwise the root logger
    # is returned, which is also used by other packages like aiormq
    if connection_id is None:
        logger_name = "my_logger_name"
    else:
        logger_name = connection_id
    logger = logging.getLogger(logger_name)
    attach_bot_log_handler(logger)
    logger.setLevel(1)
    logger = logging.LoggerAdapter(logger, extra)

    return logger
