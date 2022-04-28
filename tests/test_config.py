import dataclasses
import typing

import pytest

from glorpen.config.config import Config
from glorpen.config.fields.simple import SimpleTypes
from glorpen.config.validation import Validator


def create_config(types=None):
    return Config(validator=Validator(), types=types)


def test_default_import():
    from glorpen.config import default
    assert isinstance(default(), Config)


class TestConfig:
    def test_not_supported_value_path(self):
        c = create_config()
        with pytest.raises(ValueError, match="Could not convert to"):
            c.to_model("", str)

    def test_optional_values(self):
        c = create_config()
        assert c.to_model(None, typing.Optional[str]) is None

    def test_default_values(self):
        c = create_config()

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

    def test_too_many_properties(self):
        c = create_config()
        c.register_type(SimpleTypes)

        @dataclasses.dataclass
        class Data:
            a_prop: str

        with pytest.raises(ValueError, match="Extra field"):
            c.to_model({"a_prop": "asd", "test": "test"}, Data)

    def test_validation_with_asserts(self):
        c = create_config()
        c.register_type(SimpleTypes)

        @dataclasses.dataclass
        class Data:
            password: str
            password_repeated: str

            def validate(self):
                assert self.password == self.password_repeated, "Bad password"

        with pytest.raises(ValueError, match="Bad password"):
            c.to_model({
                "password": "test1",
                "password_repeated": "test2"
            }, Data)

    def test_validation_with_exception(self):
        c = create_config()
        c.register_type(SimpleTypes)

        @dataclasses.dataclass
        class Data:
            def validate(self):
                raise ValueError("Bad value")

        with pytest.raises(ValueError, match="Bad value"):
            c.to_model({}, Data)
