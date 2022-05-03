from semver import VersionInfo

from glorpen.config import Config
from glorpen.config.fields.version import VersionType
from glorpen.config.model.schema import Schema


def create_config() -> Config:
    return Config(schema=Schema(), types=[VersionType])


def test_version():
    assert create_config().to_model("1.2.3", VersionInfo) == VersionInfo(1, 2, 3)
