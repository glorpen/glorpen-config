import pathlib
import typing

import pytest

from glorpen.config.fields.simple import BooleanType, CollectionTypes, LiteralType, PathType, SimpleTypes
from glorpen.config.model.schema import Schema
from glorpen.config.model.transformer import Transformer
from glorpen.config.validation import Validator


def create_config(types=None):
    return Transformer(schema=Schema(), validator=Validator(), types=types)


class Dummy:
    def __str__(self):
        raise Exception('dummy exception')


class TestSimpleTypes:
    @classmethod
    def create_config(cls):
        return create_config([SimpleTypes])

    def test_int(self):
        c = self.create_config()

        assert c.to_model("10", int) is 10
        with pytest.raises(ValueError):
            c.to_model("asd", int)
        with pytest.raises(ValueError):
            c.to_model(Dummy(), int)

    def test_str(self):
        c = self.create_config()

        assert c.to_model("10", str) == "10"
        assert c.to_model(10, str) == "10"
        with pytest.raises(ValueError):
            c.to_model(Dummy(), str)

    @pytest.mark.parametrize("value", ["asd", 10, True, Dummy, Dummy()])
    def test_any(self, value):
        c = self.create_config()
        assert c.to_model(value, typing.Any) is value

    def test_list(self):
        c = self.create_config()
        assert c.to_model("abc", typing.List[str]) == ["a", "b", "c"]


class TestBooleanType:
    @classmethod
    def create_config(cls):
        return create_config([BooleanType])

    def test_bool(self):
        c = self.create_config()

        for t_value in ["yes", "YeS", "y", "t", "enable", "on", 1, True]:
            assert c.to_model(t_value, bool) is True, f"{t_value} is truthful"
        for f_value in ["no", "No", "n", "f", 0, False]:
            assert c.to_model(f_value, bool) is False, f"{f_value} is false"


class TestLiteral:
    def test_choice(self):
        c = create_config([LiteralType])

        assert c.to_model("asd", typing.Literal["asd", "qwe"]) == "asd"
        with pytest.raises(ValueError, match="Not one of"):
            c.to_model("a", typing.Literal["asd", "qwe"])


class TestPathType:
    @classmethod
    def create_config(cls):
        return create_config([PathType])

    def test_default(self):
        c = self.create_config()

        assert isinstance(c.to_model("/non/existent", pathlib.Path), pathlib.Path)
        with pytest.raises(ValueError):
            c.to_model("/non/existent", pathlib.Path, metadata={"existing": True})
        assert c.to_model("/non/../absolute", pathlib.Path, metadata={"absolute": True}) == pathlib.Path("/absolute")
        assert c.to_model("~/asd", pathlib.Path, metadata={"expand": True}).is_absolute()


class TestCollectionType:
    @classmethod
    def create_config(cls):
        return create_config([CollectionTypes, SimpleTypes])

    def test_struct(self):
        c = self.create_config()

        assert c.to_model("abc", typing.Tuple[str, str, str]) == ("a", "b", "c"), "string is iterable"
        assert c.to_model([1, 2], typing.Tuple[int, int, typing.Optional[int]]) == (1, 2, None)

        with pytest.raises(ValueError, match="No value provided"):
            assert c.to_model([1], typing.Tuple[int, int])
        with pytest.raises(ValueError, match="Extra value"):
            assert c.to_model([1, 2], typing.Tuple[int])
