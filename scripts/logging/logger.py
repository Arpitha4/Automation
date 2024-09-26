import logging
import pathlib
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from scripts.config import LoggingDetails


PROJECT_NAME = LoggingDetails.FILE_NAME
LOG_LEVEL = logging.INFO
LOG_PATH = LoggingDetails.LOG_PATH
MAX_BYTES = LoggingDetails.MAX_BYTES
BACKUP_COUNT = LoggingDetails.BACKUP_COUNT
ENABLE_FILE_LOGGING = True


def read_configuration():
    return {
        "name": PROJECT_NAME,
        "handlers": [
            {"type": "RotatingFileHandler", "max_bytes": MAX_BYTES, "back_up_count": BACKUP_COUNT},
            {"type": "StreamHandler"},
        ],
    }


def init_logger():
    logging_config = read_configuration()

    # Create a logger instance
    __logger__ = logging.getLogger(PROJECT_NAME)
    __logger__.setLevel(LOG_LEVEL)

    log_formatter = "%(asctime)s - %(levelname)-6s - [%(funcName)5s(): %(lineno)s] - %(message)s"
    time_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_formatter, time_format)

    for each_handler in logging_config["handlers"]:
        temp_handler = None

        if each_handler["type"] == "RotatingFileHandler" and ENABLE_FILE_LOGGING:
            pathlib.Path(LOG_PATH).mkdir(parents=True, exist_ok=True)
            log_file = pathlib.Path(LOG_PATH, f"{PROJECT_NAME}.log")
            temp_handler = RotatingFileHandler(
                log_file,
                maxBytes=each_handler["max_bytes"],
                backupCount=each_handler["back_up_count"],
            )
            temp_handler.setFormatter(formatter)

        elif each_handler["type"] == "StreamHandler":
            temp_handler = StreamHandler()
            temp_handler.setFormatter(formatter)

        if temp_handler:
            __logger__.addHandler(temp_handler)

    return __logger__


# Initialize the logger
logger = init_logger()
