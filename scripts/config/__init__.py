from pydantic import Field
from pydantic_settings import BaseSettings

from scripts.config.app_configurations import Path, LoggingDetails


class _Services(BaseSettings):
    LOG_LEVEL: str = LoggingDetails.LOG_LEVEL
    BACKUP_COUNT: int = LoggingDetails.BACKUP_COUNT
    MAX_BYTES: int = LoggingDetails.MAX_BYTES
    ENABLE_FILE_LOGGING: bool = True
    ENABLE_BACKUP_STORING: bool = Field(default=False, env="enable_backup")
    WORKERS: int = Field(default=1, env="workers")


class _BasePathConf(BaseSettings):
    BASE_PATH: str = "/"


class _PathConf(BaseSettings):
    LOG_PATH: str = LoggingDetails.LOG_PATH
    CONFIG_PATH: str = Path.CONFIG_PATH


Services = _Services()
PathConf = _PathConf()

__all__ = [
    "Services",
    "PathConf",
]
