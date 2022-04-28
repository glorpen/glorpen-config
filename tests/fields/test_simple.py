import typing

import pytest

from glorpen.config import Config, SimpleTypes
from glorpen.config.fields.simple import BooleanType, UnionType
from glorpen.config.validation import Validator


def create_config(types=None):
    return Config(validator=Validator(), types=types)


class Dummy:
    def __str__(self):
        raise Exception('dummy exception')


class TestSimpleTypes:
    def test_int(self):
        c = create_config([SimpleTypes])

        assert c.to_model("10", int) is 10
        with pytest.raises(ValueError):
            c.to_model("asd", int)
        with pytest.raises(ValueError):
            c.to_model(Dummy(), int)

    def test_str(self):
        c = create_config([SimpleTypes])

        assert c.to_model("10", str) == "10"
        assert c.to_model(10, str) == "10"
        with pytest.raises(ValueError):
            c.to_model(Dummy(), str)

    def test_bool(self):
        c = create_config([BooleanType])

        for t_value in ["yes", "YeS", "y", "t", "enable", "on", 1, True]:
            assert c.to_model(t_value, bool) is True, f"{t_value} is truthful"
        for f_value in ["no", "No", "n", "f", 0, False]:
            assert c.to_model(f_value, bool) is False, f"{f_value} is false"

