import dataclasses
import typing

FieldOptions = typing.Dict[str, typing.Any]


@dataclasses.dataclass
class Field:
    type: typing.Any
    options: FieldOptions = dataclasses.field(default_factory=dict)
    args: typing.Union[None, typing.Dict[str, 'Field'], typing.Sequence['Field']] = None
    default_factory: typing.Optional[typing.Callable] = None
    doc: typing.Optional[str] = None

    def has_arg_with_type(self, data):
        for arg in self.args:
            if data is arg.type:
                return True
        return False

    def is_type_subclass(self, class_or_tuple):
        return isinstance(self.type, type) and issubclass(self.type, class_or_tuple)


class Schema:
    def generate(self, tp, options=None):
        return self._any_to_field(tp, options or {})

    def _any_to_field(self, tp, options: FieldOptions):
        if dataclasses.is_dataclass(tp):
            return self._dataclass_to_field(tp)
        else:
            return self._type_to_field(tp, options)

    def _type_to_field(self, tp, options: FieldOptions):
        origin = typing.get_origin(tp)
        if origin is None:
            return Field(type=tp, options=dict(options))
        else:
            return Field(
                type=origin, options=dict(options),
                args=tuple(self._any_to_field(f, options) for f in typing.get_args(tp))
            )

    @classmethod
    def _get_default_factory(cls, field: dataclasses.Field):
        if field.default is not dataclasses.MISSING:
            return lambda: field.default
        elif field.default_factory is not dataclasses.MISSING:
            return field.default_factory
        else:
            return None

    @classmethod
    def _get_doc(cls, obj):
        if hasattr(obj, "__doc__") and obj.__doc__:
            return obj.__doc__

    def _dataclass_field_to_field(self, field: dataclasses.Field):
        options = dict(field.metadata)
        doc = options.pop("doc", None)
        ret = self._any_to_field(field.type, options=options)
        ret.default_factory = self._get_default_factory(field)
        ret.doc = doc
        return ret

    def _dataclass_to_field(self, cls):
        return Field(
            type=cls,
            args=dict((field.name, self._dataclass_field_to_field(field)) for field in dataclasses.fields(cls)),
            doc=self._get_doc(cls)
        )
