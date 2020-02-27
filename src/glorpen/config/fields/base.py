# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import contextlib
from collections import OrderedDict
from glorpen.config.exceptions import ValidationError, CircularDependency
from glorpen.config.translators.base import Help

class Value(object):
    packed = None

    def __init__(self, field):
        super().__init__()

        self.field = field

class ContainerValue(Value):
    def __init__(self, values, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.values = OrderedDict(values)

class SingleValue(Value):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.value = value

class Field(object):
    """Single field in configuration file.
    
    Custom fields should implement own normalizer/interpolation by overriding  corresponding methods.
    
    To add custom validation based on whole config object use :meth:`.validator`.
    """

    _help = None

    def __init__(self, validators=None):
        super().__init__()
        self._validators = list(validators) if validators else []

    def is_value_supported(self, raw_value) -> bool:
        raise NotImplementedError()
    
    def normalize(self, raw_value) -> OrderedDict:
        raise NotImplementedError()
    
    def get_dependencies(self, normalized_value):
        return []

    def interpolate(self, normalized_value, values):
        return normalized_value
    
    def create_packed_value(self, normalized_value):
        raise NotImplementedError()
    
    def pack(self, interpolated_value):
        packed = self.create_packed_value(interpolated_value)
        interpolated_value.packed = packed
        return packed

    def validator(self, cb):
        self._validators.append(cb)
        return self

    def validate(self, packed_value, packed_tree):
        for cb in self._validators:
            cb(packed_value, packed_tree)
    
    def help(self, **kwargs):
        self._help = Help(**kwargs)
        return self
    
    def variant(self, **kwargs):
        self._help.variant(**kwargs)
        return self

class Optional(object):
    """Field wrapper for nullable fields with defaults."""
    def __init__(self, field, default=None):
        super().__init__()
        self.field = field
        self.default = default
    
    def __getattr__(self, name):
        return getattr(self.field, name)
    
    def is_value_supported(self, raw_value):
        return raw_value is None or self.field.is_value_supported(raw_value)
    
    def normalize(self, raw_value):
        if raw_value is None:
            return self.default
        return self.field.normalize(raw_value)
    
    def get_dependencies(self, normalized_value):
        if normalized_value is None:
            return []
        return self.field.get_dependencies(normalized_value)
    
    def help(self, **kwargs):
        if "value" not in kwargs:
            kwargs["value"] = self.default
            # TODO: default value should be normalized
        return self.field.help(**kwargs)
