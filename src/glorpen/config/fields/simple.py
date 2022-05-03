import itertools
import pathlib
import typing

from glorpen.config.model.transformer import ConfigType, CollectionValueError
from glorpen.config.model import schema


class UnionType(ConfigType):
    def to_model(self, data: typing.Any, model: schema.Field):
        if model.type is typing.Union:
            return self._try_each_type(data, model.args)

    def _try_each_type(self, data, types):
        errors = []
        for tp in types:
            try:
                return self._converter(data, tp)
            except ValueError as e:
                errors.append(e)

        raise CollectionValueError(errors)


class SimpleTypes(ConfigType):
    @classmethod
    def _try_convert(cls, data, conv):
        try:
            return conv(data)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"{e.__class__.__name__}: {e}")

    def to_model(self, data: typing.Any, model: schema.Field):
        if model.type in (int, str, float, list):
            return self._try_convert(data, model.type)
        if model.type is typing.Any:
            return data


class BooleanType(ConfigType):
    _truthful = [
        "true",
        "t",
        1,
        "y",
        "yes",
        "on",
        "enable",
        True
    ]

    def to_model(self, data: typing.Any, model: schema.Field):
        if model.type is bool:
            if isinstance(data, str):
                data = data.lower()
            return self.is_truthful(data)

    def is_truthful(self, value):
        return value in self._truthful


class CollectionTypes(ConfigType):
    def to_model(self, data: typing.Any, model: schema.Field):
        if model.type is tuple:
            errors = {}
            ret = []

            for index, (field, value) in enumerate(itertools.zip_longest(model.args, data)):
                try:
                    ret.append(self._converter(value, field))
                except Exception as e:
                    errors[index] = e

            for i in range(len(model.args), len(data)):
                errors[i + 1] = ValueError("Extra value")

            if errors:
                raise CollectionValueError(errors)

            return tuple(ret)


class LiteralType(ConfigType):
    def to_model(self, data: typing.Any, model: schema.Field):
        if model.type is typing.Literal:
            if model.has_arg_with_type(data):
                return data

            raise ValueError("Not one of: " + ', '.join(repr(a) for a in model.args))


class PathType(ConfigType):
    def to_model(self, data: typing.Any, model: schema.Field):
        if model.is_type_subclass(pathlib.Path):
            p = pathlib.Path(data)

            try:
                if model.options.get("expand", False):
                    p = p.expanduser()
                if model.options.get("absolute", False):
                    p = p.resolve()
            except RuntimeError as e:
                raise ValueError(e)

            if model.options.get("existing", False):
                try:
                    p.resolve(True)
                except OSError as e:
                    raise ValueError(e)

            return p
