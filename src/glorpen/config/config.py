# from glorpen.config.fields import path_validation_error
import abc
import dataclasses
import itertools
import textwrap
import types
import typing

_NoneType = types.NoneType if hasattr(types, "NoneType") else type(None)


class ConfigType(abc.ABC):
    def __init__(self, config):
        super(ConfigType, self).__init__()
        self.config = config

    @abc.abstractmethod
    def as_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict, path: str):
        pass


ValueErrorItems = typing.Union[dict, typing.Sequence]


class ConfigValueError(ValueError):
    def __init__(self, error):
        super(ConfigValueError, self).__init__(f"Found validation errors:\n{error}")


class DictValueError(ValueError):
    def __init__(self, items: ValueErrorItems):
        # msg = "Invalid fields.\n" + self._format_row(items)
        msg = self._format_row(items)
        super(DictValueError, self).__init__(msg)

    def _format_row(self, items: ValueErrorItems):
        return textwrap.indent("\n".join(self._format_items(items)), "")

    def _format_items(self, items: ValueErrorItems):
        if hasattr(items, "keys"):
            key_max_len = max(len(str(i)) for i in items.keys())
            item_sets = items.items()
            key_suffix = ": "
        else:
            key_max_len = 1
            item_sets = [("-", v) for v in items]
            key_suffix = " "

        msg_offset = key_max_len + len(key_suffix)

        for k, e in item_sets:
            f_key = str(k).rjust(key_max_len)
            f_msg = textwrap.indent(str(e), " " * msg_offset)[msg_offset:]
            yield f"{f_key}{key_suffix}{f_msg}"


class Config:
    """Config validator and normalizer."""

    _registered_types: typing.List[ConfigType]

    def __init__(self):
        super(Config, self).__init__()

        self._registered_types = []

    @classmethod
    def _handle_optional_values(cls, type, default_factory):
        if (type is _NoneType) or (typing.get_origin(type) is typing.Union and _NoneType in typing.get_args(type)):
            return None
        if default_factory:
            return default_factory()

        raise ValueError("No value provided")

    def as_model(self, data: typing.Any, type, metadata=None, default_factory=None, path=""):
        if data is None:
            return self._handle_optional_values(type, default_factory)

        if dataclasses.is_dataclass(type):
            return self._from_dataclass(data, type, path=path)
        else:
            origin = typing.get_origin(type)
            if origin is None:
                return self._from_type(data=data, type=type, args=(), metadata=metadata, path=path)
            else:
                return self._from_type(data=data, type=origin, args=typing.get_args(type), metadata=metadata, path=path)

    def to_model(self, data, cls):
        try:
            return self.as_model(data, cls)
        except ValueError as e:
            raise ConfigValueError(e) from None

    @classmethod
    def _get_default_factory(cls, field: dataclasses.Field):
        if field.default is not dataclasses.MISSING:
            return lambda: field.default
        elif field.default_factory is not dataclasses.MISSING:
            return field.default_factory
        else:
            return None

    def _from_dataclass(self, data: typing.Dict, cls, path: str):
        kwargs = {}
        errors = {}
        for field in dataclasses.fields(cls):
            try:
                kwargs[field.name] = self.as_model(data.get(field.name), field.type, metadata=field.metadata,
                    default_factory=self._get_default_factory(field), path=f"{path}.{field.name}")
            except ValueError as e:
                errors[field.name] = e

        if errors:
            raise DictValueError(errors)

        return cls(**kwargs)

    def _from_type(self, data: typing.Any, type, args: typing.Tuple, metadata: dict, path: str):
        for reg_type in self._registered_types:
            value = reg_type.as_model(data=data, type=type, args=args, metadata=metadata, path=path)
            if value is not None:
                return value

        raise ValueError(f"Could not convert to {type}")

    def register(self, type: ConfigType):
        self._registered_types.append(type(self))


class UnionType(ConfigType):
    def as_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict, path: str):
        if type is typing.Union:
            return self._try_each_type(data, args, metadata=metadata, path=path)

    def _try_each_type(self, data, types, path: str, metadata=None):
        errors = []
        for tp in types:
            try:
                return self.config.as_model(data, tp, metadata=metadata, path=path)
            except ValueError as e:
                errors.append(e)

        raise DictValueError(errors)


class SimpleTypes(ConfigType):
    @classmethod
    def _try_convert(cls, data, conv):
        try:
            return conv(data)
        except Exception as e:
            raise ValueError(e)

    def as_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict, path: str):
        if type in (int, str, bool, float):
            return self._try_convert(data, type)


class SequenceTypes(ConfigType):
    def as_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict, path: str):
        if type is tuple:
            errors = {}
            ret = []

            for index, (tp, value) in enumerate(itertools.zip_longest(args, data)):
                try:
                    ret.append(self.config.as_model(value, tp, path=f"{path}.{index}"))
                except Exception as e:
                    errors[index] = e

            if errors:
                raise DictValueError(errors)

            return tuple(ret)


def default():
    c = Config()
    c.register(UnionType)
    c.register(SimpleTypes)
    c.register(SequenceTypes)

    return c

