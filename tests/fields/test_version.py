from semver import VersionInfo

from glorpen.config import Config
from glorpen.config.fields.version import VersionType


def create_config() -> Config:
    return Config(types=[VersionType])


def test_version():
    assert create_config().to_model("1.2.3", VersionInfo) == VersionInfo(1, 2, 3)
