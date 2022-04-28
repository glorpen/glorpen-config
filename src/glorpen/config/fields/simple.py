import itertools
import typing

from glorpen.config.config import ConfigType, CollectionValueError


class UnionType(ConfigType):
    def to_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict):
        if type is typing.Union:
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
        except Exception as e:
            raise ValueError(e)

    def to_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict):
        if type in (int, str, bool, float):
            return self._try_convert(data, type)


class CollectionTypes(ConfigType):
    def to_model(self, data: typing.Any, type, args: typing.Tuple, metadata: dict):
        if type is tuple:
            errors = {}
            ret = []

            for index, (tp, value) in enumerate(itertools.zip_longest(args, data)):
                try:
                    ret.append(self._converter(value, tp))
                except Exception as e:
                    errors[index] = e

            for i in range(len(args), len(data)):
                errors[i+1] = ValueError("Extra value")

            if errors:
                raise CollectionValueError(errors)

            return tuple(ret)

#
# class PathObj(Path):
#     """Converts value to :class:`pathlib.Path` object."""
#
#     def normalize(self, raw_value):
#         normalized_value = super(PathObj, self).normalize(raw_value)
#         normalized_value.value = pathlib.Path(normalized_value.value)
#         return normalized_value
#
#     def get_dependencies(self, normalized_value):
#         sv = SingleValue(str(normalized_value.value), self)
#         return super().get_dependencies(sv)
#
#     def interpolate(self, normalized_value, values):
#         sv = SingleValue(str(normalized_value.value), self)
#         interpolated = super().interpolate(sv, values)
#         return pathlib.Path(interpolated)
#
# class List(Field):
#     """Converts value to list."""
#
#     default_value = []
#     help_class = ContainerHelp
#
#     def __init__(self, schema, check_values=False, **kwargs):
#         super(List, self).__init__(**kwargs)
#
#         self._schema = schema
#         self._check_values = check_values
#
#         self.help_config.set_children([self._schema.help_config])
#
#     def normalize(self, raw_value):
#         values = []
#         for i,v in enumerate(raw_value):
#             with exceptions.path_error(key=i):
#                 values.append((i, self._schema.normalize(v)))
#
#         return ContainerValue(values, self)
#
#     def is_value_supported(self, raw_value):
#         if not isinstance(raw_value, (tuple, list)):
#             return False
#         if self._check_values:
#             for i in raw_value:
#                 if not self._schema.is_value_supported(i):
#                     return False
#         return True
#
#     def create_packed_value(self, interpolated_value):
#         ret = []
#         for k,i in interpolated_value.values.items():
#             with exceptions.path_error(key=k):
#                 ret.append(self._schema.pack(i))
#         return tuple(ret)
#
# class Any(Field):
#     """Field that accepts any value."""
#     def is_value_supported(self, raw_value):
#         return True
#     def create_packed_value(self, normalized_value):
#         return normalized_value.value
#     def normalize(self, raw_value):
#         return SingleValue(raw_value, self)
#
# class Bool(Field):
#     truthful = [
#         "true",
#         "True",
#         "t",
#         1,
#         "y",
#         "yes",
#         "on",
#         True
#     ]
#     def is_value_supported(self, raw_value):
#         return True
#     def normalize(self, raw_value):
#         return SingleValue(raw_value in self.truthful, self)
#     def create_packed_value(self, normalized_value):
#         return normalized_value.value
#
# class Choice(Field):
#     def __init__(self, choices):
#         super().__init__()
#
#         self._choices = choices
#
#     def is_value_supported(self, raw_value):
#         try:
#             hash(raw_value)
#         except TypeError:
#             return False
#         return True
#
#     def normalize(self, raw_value):
#         if raw_value not in self._choices:
#             raise Exception("Unsupported value %r" % raw_value)
#
#         if isinstance(self._choices, (tuple, list)):
#             v = raw_value
#         else:
#             v = self._choices[raw_value]
#
#         return SingleValue(v, self)
#
#     def create_packed_value(self, normalized_value):
#         return normalized_value.value
