import logging

from glorpen.config import Config
from glorpen.config.fields.log import LogLevelType, LogLevel


def create_config() -> Config:
    return Config(types=[LogLevelType])


def test_level():
    assert create_config().to_model("WARNING", LogLevel) == logging.WARNING
