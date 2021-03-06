# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import os
import re
import pathlib
from collections import OrderedDict
from glorpen.config import exceptions
from glorpen.config.fields.base import Field, SingleValue, ContainerValue, Optional, is_optional
from glorpen.config.translators.base import ContainerHelp

def take_a_few(iterable, count):
    i = 0
    while i < count:
        yield next(iterable)
        i+=1

class Dict(Field):
    """Converts values to :class:`collections.OrderedDict`
    
    Supports setting whole schema (specific keys and specific values)
    or just keys type and values type.
    
    Keys can be interpolated if ``keys`` param supports it.
    """
    
    default_value = {}
    help_class = ContainerHelp

    _schema = None
    _key_field = None
    _value_field = None
    
    def __init__(self, schema=None, keys=None, values=None, check_keys=False, **kwargs):
        """
        To set specific schema pass dict to schema argument: ``{"param1": SomeField()}``.
        
        To specify keys and values type use keys and values arguments: ``Dict(keys=String(), values=Number())``. 
        """
        super(Dict, self).__init__(**kwargs)

        self._check_keys = check_keys
        
        help_items = {}
        if schema is None:
            self._key_field = keys or String()
            self._value_field = values
        else:
            self._schema = schema
            for k,v in schema.items():
                help_items[k] = v.help_config
        
        # TODO: implement support for key/value schema
        self.help_config.set_children(help_items)
    
    def normalize(self, raw_value):
        # when all subkeys are optional, parent can be omitted
        if raw_value is None:
            raw_value = OrderedDict()
        
        if self._schema:
            v = self._check_keys_with_schema(raw_value)
            v = self._normalize_with_schema(v)
        else:
            v = self._normalize(raw_value)
        
        return ContainerValue(v, self)

    def _check_keys_with_schema(self, raw_value):
        spec_blanks = set()
        spec=set(self._schema.keys())
        val_keys = set(raw_value.keys())
        
        for def_k, def_v in self._schema.items():
            if is_optional(def_v):
                spec_blanks.add(def_k)
        
        diff_new = val_keys.difference(spec)
        diff_missing = spec.difference(val_keys).difference(spec_blanks)
        msgs = []
        
        if diff_new or diff_missing:
            if diff_missing:
                msgs.append("missing keys %r" % diff_missing)
            if diff_new:
                msgs.append("excess keys %r" % diff_new)
        
        for k in val_keys.intersection(spec):
            if not self._schema[k].is_value_supported(raw_value[k]):
                msgs.append("value for %r is not supported" % k)

        if msgs:
            raise exceptions.ConfigException("Found following errors: %s" % ", ".join(msgs))
        
        return raw_value
    
    def _normalize_with_schema(self, raw_value):
        ret = OrderedDict()
        for k,field in self._schema.items():
            with exceptions.path_error(key=k):
                ret[k] = field.normalize(raw_value.get(k))
        return ret
    
    def _normalize(self, raw_value):
        ret = OrderedDict()
        
        for k,v in raw_value.items():
            with exceptions.path_error(key=k):
                ret[self._key_field.normalize(k)] = self._value_field.normalize(v)
        
        return ret
    
    def is_value_supported(self, raw_value):
        if not isinstance(raw_value, (dict,)):
            return False
        
        if self._check_keys:
            if self._schema:
                for k,f in self._schema.items():
                    if not is_optional(f) and k not in raw_value:
                        return False
            else:
                for k in raw_value.keys() and not self._key_field.is_value_supported(k):
                    return False
        
        return True
    
    def create_packed_value(self, normalized_value):
        ret = OrderedDict()
        for k,v in normalized_value.values.items():
            with exceptions.path_error(key=k):
                rk = k.field.pack(k) if self._key_field else k
                ret[rk] = v.field.pack(v)

        return ret
    
    def get_dependencies(self, normalized_value):
        ret = []
        if self._key_field:
            for k in normalized_value.values.keys():
                ret.extend(self._key_field.get_dependencies(k))
        return ret
    
    def interpolate(self, normalized_value, values):
        if self._key_field:
            i = iter(values)
            for k in normalized_value.values.keys():
                deps_count = len(self._key_field.get_dependencies(k))
                if deps_count:
                    vk = tuple(take_a_few(i, deps_count))
                    self._key_field.interpolate(k, vk)
        else:
            raise NotImplementedError()
    
class String(Field):
    """Converts value to string."""

    def __init__(self, *args, split_by=".", left_char="{", right_char="}", **kwargs):
        super().__init__(*args, **kwargs)

        self._split_by = split_by

        left_char = re.escape(left_char)
        right_char = re.escape(right_char)
        self._re_part = re.compile(f'{left_char}\\s*(.*?)\\s*{right_char}')
        self._re_number = re.compile(r'(.*)\[(.*?)\]')
    
    def normalize(self, raw_value):
        try:
            return SingleValue(str(raw_value), self)
        except Exception as e:
            raise exceptions.ConfigException("Could not convert %r to string, got %r" % (raw_value, e))
    
    def create_packed_value(self, normalized_value):
        return normalized_value.value
    
    def is_value_supported(self, raw_value):
        return isinstance(raw_value, (str,))
    
    def get_as_path(self, s):
        ret = []
        for j in s.split(self._split_by):
            d = self._re_number.match(j)
            if d:
                if d.group(1) != "":
                    ret.append(d.group(1))
                k = float(d.group(2))
            else:
                k = j
            ret.append(k)
        return tuple(ret)

    def get_dependencies(self, normalized_value):
        return tuple(self.get_as_path(i) for i in self._re_part.findall(normalized_value.value))
    
    def interpolate(self, normalized_value, values):
        i = iter(values)
        def replace(matchobj):
            return str(next(i))
        normalized_value.value = self._re_part.sub(replace, normalized_value.value)

class Reference(String):
    def interpolate(self, normalized_value, values):
        return values[0]
    def get_dependencies(self, normalized_value):
        return self.get_as_path(normalized_value)

class Path(String):
    """Converts given value to disk path."""
    
    def normalize(self, raw_value):
        normalized_value = super(Path, self).normalize(raw_value)
        normalized_value.value = os.path.realpath(normalized_value.value)
        return normalized_value
    
class PathObj(Path):
    """Converts value to :class:`pathlib.Path` object."""
    
    def normalize(self, raw_value):
        normalized_value = super(PathObj, self).normalize(raw_value)
        normalized_value.value = pathlib.Path(normalized_value.value)
        return normalized_value
    
    def get_dependencies(self, normalized_value):
        sv = SingleValue(str(normalized_value.value), self)
        return super().get_dependencies(sv)
    
    def interpolate(self, normalized_value, values):
        sv = SingleValue(str(normalized_value.value), self)
        interpolated = super().interpolate(sv, values)
        return pathlib.Path(interpolated)

class List(Field):
    """Converts value to list."""

    default_value = []
    help_class = ContainerHelp
    
    def __init__(self, schema, check_values=False, **kwargs):
        super(List, self).__init__(**kwargs)
        
        self._schema = schema
        self._check_values = check_values

        self.help_config.set_children([self._schema.help_config])
    
    def normalize(self, raw_value):
        values = []
        for i,v in enumerate(raw_value):
            with exceptions.path_error(key=i):
                values.append((i, self._schema.normalize(v)))
        
        return ContainerValue(values, self)
    
    def is_value_supported(self, raw_value):
        if not isinstance(raw_value, (tuple, list)):
            return False
        if self._check_values:
            for i in raw_value:
                if not self._schema.is_value_supported(i):
                    return False
        return True
    
    def create_packed_value(self, interpolated_value):
        ret = []
        for k,i in interpolated_value.values.items():
            with exceptions.path_error(key=k):
                ret.append(self._schema.pack(i))
        return tuple(ret)
    
class Variant(Field):
    """Converts value to normalized state using one :class:`.Field` chosen from multiple provided.
    
    To allow blank values you have to pass child field with enabled blank values.
    First field which supports value (:meth:`.Field.is_value_supported`) will be used to convert it.
    """

    help_class = ContainerHelp

    def __init__(self, schema, *args, **kwargs):
        super(Variant, self).__init__(*args, **kwargs)
        self._values_fields = schema
        self.help_config.set_children(*[f.help_config for f in schema])
    
    def normalize(self, raw_value):
        return self._get_matching_field(raw_value).normalize(raw_value)
    
    def _get_matching_field(self, raw_value):
        for f in self._values_fields:
            if f.is_value_supported(raw_value):
                return f

    def is_value_supported(self, raw_value):
        if self._get_matching_field(raw_value):
            return True
        return False
    
    def create_packed_value(self, normalized_value):
        return normalized_value.field.pack(normalized_value)
    
    def interpolate(self, normalized_value, values):
        return normalized_value.field.interpolate(normalized_value, values)
    
    def get_dependencies(self, normalized_value):
        return normalized_value.field.get_dependencies(normalized_value)

class Any(Field):
    """Field that accepts any value."""
    def is_value_supported(self, raw_value):
        return True
    def create_packed_value(self, normalized_value):
        return normalized_value.value
    def normalize(self, raw_value):
        return SingleValue(raw_value, self)


class Number(Field):
    """Converts value to numbers."""
    
    def is_value_supported(self, value):
        try:
            float(value)
        except (ValueError, TypeError):
            return False
        
        return True
    
    def normalize(self, raw_value):
        return SingleValue(float(raw_value), self)
    def create_packed_value(self, normalized_value):
        return normalized_value.value

class Bool(Field):
    truthful = [
        "true",
        "True",
        "t",
        1,
        "y",
        "yes",
        "on",
        True
    ]
    def is_value_supported(self, raw_value):
        return True
    def normalize(self, raw_value):
        return SingleValue(raw_value in self.truthful, self)
    def create_packed_value(self, normalized_value):
        return normalized_value.value

class Choice(Field):
    def __init__(self, choices):
        super().__init__()

        self._choices = choices
        
    def is_value_supported(self, raw_value):
        try:
            hash(raw_value)
        except TypeError:
            return False
        return True
    
    def normalize(self, raw_value):
        if raw_value not in self._choices:
            raise Exception("Unsupported value %r" % raw_value)

        if isinstance(self._choices, (tuple, list)):
            v = raw_value
        else:
            v = self._choices[raw_value]
            
        return SingleValue(v, self)
    
    def create_packed_value(self, normalized_value):
        return normalized_value.value
