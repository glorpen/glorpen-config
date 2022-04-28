import itertools
import pathlib
import typing

from glorpen.config.config import ConfigType, CollectionValueError


class UnionType(ConfigType):
    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        if tp is typing.Union:
            return self._try_each_type(data, args, metadata=metadata)

    def _try_each_type(self, data, types, metadata=None):
        errors = []
        for tp in types:
            try:
                return self._converter(data, tp, metadata=metadata)
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

    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        if tp in (int, str, float, list):
            return self._try_convert(data, tp)
        if tp is typing.Any:
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

    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        if tp is bool:
            if isinstance(data, str):
                data = data.lower()
            return self.is_truthful(data)

    def is_truthful(self, value):
        return value in self._truthful


class CollectionTypes(ConfigType):
    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        if tp is tuple:
            errors = {}
            ret = []

            for index, (tp, value) in enumerate(itertools.zip_longest(args, data)):
                try:
                    ret.append(self._converter(value, tp))
                except Exception as e:
                    errors[index] = e

            for i in range(len(args), len(data)):
                errors[i + 1] = ValueError("Extra value")

            if errors:
                raise CollectionValueError(errors)

            return tuple(ret)


class LiteralType(ConfigType):
    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        if data in args:
            return data

        raise ValueError("Not one of: " + ', '.join(repr(a) for a in args))


class PathType(ConfigType):
    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        p = pathlib.Path(data)

        try:
            if metadata.get("expand", False):
                p = p.expanduser()
            if metadata.get("absolute", False):
                p = p.resolve()
        except RuntimeError as e:
            raise ValueError(e)

        if metadata.get("existing", False):
            try:
                p.resolve(True)
            except OSError as e:
                raise ValueError(e)

        return p
