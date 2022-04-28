import abc
import dataclasses
import textwrap
import types
import typing

from glorpen.config.validation import Validator

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

    @classmethod
    def _format_items(cls, items: ValueErrorItems):
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

    def __init__(self, validator: typing.Optional[Validator], types: typing.Iterable[typing.Type[ConfigType]] = None):
        super(Config, self).__init__()

        self._registered_types = []
        self._validator = validator

        if types:
            for t in types:
                self.register_type(t)

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

        instance = cls(**kwargs)
        if self._validator:
            self._validator.validate(instance)
        return instance

    def _from_type(self, data: typing.Any, type, args: typing.Tuple, metadata: dict, path: str):
        for reg_type in self._registered_types:
            value = reg_type.as_model(data=data, type=type, args=args, metadata=metadata, path=path)
            if value is not None:
                return value

        raise ValueError(f"Could not convert to {type}")

    def register_type(self, type_cls: typing.Type[ConfigType]):
        self._registered_types.append(type_cls(self))
