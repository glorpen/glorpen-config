import typing

import semver

from glorpen.config.config import ConfigType
from glorpen.config.fields.utils import is_class_a_subclass


class Version(ConfigType):
    """Converts values to :class:`semver.VersionInfo`"""

    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        if is_class_a_subclass(tp, semver.VersionInfo):
            return semver.VersionInfo.parse(str(data))
