import logging

from glorpen.config.fields.log import LogLevel, LogLevelType
from glorpen.config.model.schema import Schema
from glorpen.config.model.transformer import Transformer


def create_config() -> Transformer:
    return Transformer(schema=Schema(), types=[LogLevelType])


def test_level():
    assert create_config().to_model("WARNING", LogLevel) == logging.WARNING
