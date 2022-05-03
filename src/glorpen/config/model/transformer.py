import abc
import dataclasses
import textwrap
import typing

from glorpen.config.model.schema import Field, Schema
from glorpen.config.validation import Validator


class DataConverter(typing.Protocol):
    def __call__(self, data: typing.Any, model: Field):
        pass


class ConfigType(abc.ABC):
    def __init__(self, converter: DataConverter):
        super(ConfigType, self).__init__()
        self._converter = converter

    @abc.abstractmethod
    def to_model(self, data: typing.Any, model: Field):
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


class Transformer:
    """Config normalizer."""

    _validator: typing.Optional[Validator]
    _registered_types: typing.List[ConfigType]

    def __init__(self, schema: Schema,
                 validator: typing.Optional[Validator] = None,
                 types: typing.Optional[typing.Iterable[typing.Type[ConfigType]]] = None):
        super(Transformer, self).__init__()

        self._schema = schema
        self._registered_types = []
        self._validator = validator

        if types:
            for t in types:
                self.register_type(t)

    @classmethod
    def _handle_optional_values(cls, model: Field):
        if model.is_nullable():
            return None
        if model.default_factory:
            return model.default_factory()

        raise ValueError("No value provided")

    def _as_model(self, data: typing.Any, model: Field):
        if data is None:
            return self._handle_optional_values(model)

        if hasattr(model.args, "items"):
            return self._from_named_fields(data, model)
        else:
            return self._from_type(data, model)

    def to_model(self, data, cls, metadata=None):
        model = self._schema.generate(cls, metadata)
        try:
            return self._as_model(data, model)
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

    def _from_named_fields(self, data: typing.Dict, model: Field):
        kwargs = {}
        errors = {}
        known_fields = set()
        for field_name, field in model.args.items():
            known_fields.add(field_name)
            try:
                kwargs[field_name] = self._as_model(data.get(field_name), field)
            except ValueError as e:
                errors[field_name] = e

        for extra_field in set(data.keys()).difference(known_fields):
            errors[extra_field] = ValueError("Extra field")

        if errors:
            raise CollectionValueError(errors)

        instance = model.type(**kwargs)
        if self._validator:
            self._validator.validate(instance)
        return instance

    def _from_type(self, data: typing.Any, model: Field):
        for reg_type in self._registered_types:
            value = reg_type.to_model(data=data, model=model)
            if value is not None:
                return value

        raise ValueError(f"Could not convert to {type}")

    def register_type(self, type_cls: typing.Type[ConfigType]):
        self._registered_types.insert(0, type_cls(self._as_model))
