import logging
import typing

from glorpen.config.model.transformer import ConfigType
from glorpen.config.model.schema import Field


class LogLevel(int):
    pass


def _find_levels():
    if hasattr(logging, "_levelNames"):
        return dict((n, v) for n, v in logging._levelNames.items() if isinstance(v, int))
    if hasattr(logging, "_nameToLevel"):
        return logging._nameToLevel
    if hasattr(logging, "_nameToLevel"):
        return logging._nameToLevel

    raise ImportError("Could not find logging level names")


_levels = _find_levels()


class LogLevelType(ConfigType):
    """Converts log level name to internal number for use with :mod:`logging`"""

    _levels = None

    def to_model(self, data: typing.Any, model: Field):
        if model.is_type_subclass(LogLevel):
            value = str(data).upper()

            if value in _levels.keys():
                return _levels[value]
            else:
                raise ValueError(f"Not one of %r" % _levels.keys())
