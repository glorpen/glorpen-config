import logging
import typing

from glorpen.config.config import ConfigType


class LogLevel(ConfigType):
    """Converts log level name to internal number for use with :mod:`logging`"""

    _levels = None

    @classmethod
    def _find_levels(self):
        if hasattr(logging, "_levelNames"):
            return dict((n, v) for n, v in logging._levelNames.items() if isinstance(v, int))
        if hasattr(logging, "_nameToLevel"):
            return logging._nameToLevel
        if hasattr(logging, "_nameToLevel"):
            return logging._nameToLevel

        raise RuntimeError("Could not find logging level names")

    @classmethod
    def _get_levels(cls):
        if cls._levels is None:
            cls._levels = cls._find_levels()

        return cls._levels

    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        levels = self._get_levels()
        value = str(data).upper()

        if value in levels.keys():
            return levels[value]
        else:
            raise ValueError(f"Not one of %r" % levels.keys())
