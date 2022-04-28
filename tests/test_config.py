import dataclasses
import typing

import pytest

from glorpen.config.config import Config


class TestConfig:
    def test_not_supported_value_path(self):
        c = Config()
        with pytest.raises(ValueError, match="Could not convert to"):
            c.to_model("", str)

    def test_optional_values(self):
        c = Config()
        assert c.to_model(None, typing.Optional[str]) is None

    def test_default_values(self):
        c = Config()

        @dataclasses.dataclass
        class Data:
            default_field: str = dataclasses.field(default="default-value")
            factory_field: str = dataclasses.field(default_factory=lambda: "default-value")
            value_field: str = "default-value"
            optional_field: typing.Optional[str] = "default-value"

        m: Data = c.to_model({}, Data)

        assert m.default_field == "default-value"
        assert m.factory_field == "default-value"
        assert m.value_field == "default-value"
        assert m.optional_field is None
