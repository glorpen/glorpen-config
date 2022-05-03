from semver import VersionInfo

from glorpen.config.fields.version import VersionType
from glorpen.config.model.schema import Schema
from glorpen.config.model.transformer import Transformer


def create_config():
    return Transformer(schema=Schema(), types=[VersionType])


def test_version():
    assert create_config().to_model("1.2.3", VersionInfo) == VersionInfo(1, 2, 3)
