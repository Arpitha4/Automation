"""
This file exposes configurations from config file and environments as Class Objects
"""

import os.path
import sys
from configparser import BasicInterpolation, ConfigParser


class EnvInterpolation(BasicInterpolation):
    """
    Interpolation which expands environment variables in values.
    """

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)

        if not os.path.expandvars(value).startswith("$"):
            return os.path.expandvars(value)
        else:
            return

try:
    config = ConfigParser(interpolation=EnvInterpolation())

    current_file_path = os.path.abspath(__file__)
    project_parent_path = current_file_path

    for _ in range(3):
        project_parent_path = os.path.dirname(project_parent_path)
    config_path = os.path.join(project_parent_path, 'conf/application.conf')
    config.read(config_path)
except Exception as e:
    print(f"Error while loading the config: {e}")
    print("Failed to Load Configuration. Exiting!!!")
    sys.stdout.flush()
    sys.exit()


class LoggingDetails:
    LOG_PATH: str = config["LOGGING"]["LOG_PATH"]
    LOG_LEVEL: str = config["LOGGING"]["LOG_LEVEL"]
    BACKUP_COUNT: int = int(config["LOGGING"]["BACKUP_COUNT"])
    MAX_BYTES: int = int(config["LOGGING"]["MAX_BYTES"])
    FILE_NAME: str = config["LOGGING"]["FILE_NAME"]


class Path:
    CONFIG_PATH: str = config["PATH"]["CONFIG_PATH"]


class EnvironmentDetails:
    AUTH_ENDPOINT: str = config["ENVIRONMENT"]["AUTH_ENDPOINT"]
    BASE_PATH: str = config["ENVIRONMENT"]["BASE_PATH"]
    PROJECT_ID: str = config["ENVIRONMENT"]["PROJECT_ID"]
    tz: str = config["ENVIRONMENT"]["tz"]
    encrypt_payload: str = config["ENVIRONMENT"]["encrypt_payload"]
    app_id: str = config["ENVIRONMENT"]["app_id"]
    project_name: str = config["ENVIRONMENT"]["project_name"]
    access_token: str = config["ENVIRONMENT"]["access_token"]
