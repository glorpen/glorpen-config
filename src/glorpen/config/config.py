import abc
import dataclasses
import textwrap
import types
import typing

from glorpen.config.validation import Validator

_NoneType = types.NoneType if hasattr(types, "NoneType") else type(None)


class DataConverter(typing.Protocol):
    def __call__(self, data: typing.Any, type, metadata=None, default_factory=None):
        pass


class ConfigType(abc.ABC):
    def __init__(self, converter: DataConverter):
        super(ConfigType, self).__init__()
        self._converter = converter

    @abc.abstractmethod
    def to_model(self, data: typing.Any, tp, args: typing.Tuple, metadata: dict):
        pass


ValueErrorItems = typing.Union[dict, typing.Sequence]


class ConfigValueError(ValueError):
    def __init__(self, error):
        super(ConfigValueError, self).__init__(f"Found validation errors:\n{error}")


class CollectionValueError(ValueError):
    def __init__(self, items: ValueErrorItems):
        msg = self._format_row(items)
        super(CollectionValueError, self).__init__(msg)

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

    _validator: typing.Optional[Validator]
    _registered_types: typing.List[ConfigType]

    def __init__(self, validator: typing.Optional[Validator] = None, types: typing.Optional[typing.Iterable[typing.Type[ConfigType]]] = None):
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

    def _as_model(self, data: typing.Any, type, metadata=None, default_factory=None):
        if data is None:
            return self._handle_optional_values(type, default_factory)

        if dataclasses.is_dataclass(type):
            return self._from_dataclass(data, type)
        else:
            origin = typing.get_origin(type)
            if metadata is None:
                metadata = {}
            if origin is None:
                return self._from_type(data=data, type=type, args=(), metadata=metadata)
            else:
                return self._from_type(data=data, type=origin, args=typing.get_args(type), metadata=metadata)

    def to_model(self, data, cls, metadata=None):
        try:
            return self._as_model(data, cls, metadata=metadata)
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

    def _from_dataclass(self, data: typing.Dict, cls):
        kwargs = {}
        errors = {}
        known_fields = set()
        for field in dataclasses.fields(cls):
            known_fields.add(field.name)
            try:
                kwargs[field.name] = self._as_model(data.get(field.name), field.type, metadata=field.metadata,
                    default_factory=self._get_default_factory(field))
            except ValueError as e:
                errors[field.name] = e

        for extra_field in set(data.keys()).difference(known_fields):
            errors[extra_field] = ValueError("Extra field")

        if errors:
            raise CollectionValueError(errors)

        instance = cls(**kwargs)
        if self._validator:
            self._validator.validate(instance)
        return instance

    def _from_type(self, data: typing.Any, type, args: typing.Tuple, metadata: dict):
        for reg_type in self._registered_types:
            value = reg_type.to_model(data=data, tp=type, args=args, metadata=metadata)
            if value is not None:
                return value

        raise ValueError(f"Could not convert to {type}")

    def register_type(self, type_cls: typing.Type[ConfigType]):
        self._registered_types.insert(0, type_cls(self._as_model))
