import dataclasses
import typing

import pytest

from glorpen.config.config import Config
from glorpen.config.fields.simple import SimpleTypes


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

    def test_validation_with_asserts(self):
        c = Config()
        c.register(SimpleTypes)

        @dataclasses.dataclass
        class Data:
            password: str
            password_repeated: str

            def _validate(self):
                assert self.password == self.password_repeated, "Bad password"

        with pytest.raises(ValueError, match="Bad password"):
            c.to_model({
                "password": "test1",
                "password_repeated": "test2"
            }, Data)

    def test_validation_with_exception(self):
        c = Config()
        c.register(SimpleTypes)

        @dataclasses.dataclass
        class Data:
            def _validate(self):
                raise ValueError("Bad value")

        with pytest.raises(ValueError, match="Bad value"):
            c.to_model({}, Data)
