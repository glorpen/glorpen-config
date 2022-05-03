import typing

import semver

from glorpen.config.config import ConfigType
from glorpen.config.model.schema import Field


class VersionType(ConfigType):
    """Converts values to :class:`semver.VersionInfo`"""

    def to_model(self, data: typing.Any, model: Field):
        if model.is_type_subclass(semver.VersionInfo):
            return semver.VersionInfo.parse(str(data))
