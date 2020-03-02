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

        if not isinstance(field, (Field,)):
            raise Exception("Value %r passed as field is not a field" % field)
        
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

    # used by Optional wrapper
    default_value = None

    def __init__(self, validators=None):
        super().__init__()
        self._validators = list(validators) if validators else []

    def is_value_supported(self, raw_value) -> bool:
        raise NotImplementedError()
    
    def normalize(self, raw_value) -> Value:
        raise NotImplementedError()
    
    def get_dependencies(self, normalized_value):
        """
        Find parts that can be interpolated and return required deps.
        Should check only own data, no nested fields.
        """
        return []

    def interpolate(self, normalized_value, values) -> None:
        """
        Should replace data in normalized_value with interpolated one.
        Called only when ``get_dependencies`` finds something.
        """
        raise NotImplementedError()
    
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

class Unset(): pass

class Optional(Field):
    """Field wrapper for nullable fields with defaults."""
    def __init__(self, field, default=Unset):
        super().__init__()
        self.field = field
        
        if default is Unset:
            default = field.default_value
        self.default = default
    
    
    def is_value_supported(self, raw_value):
        return raw_value is None or self.field.is_value_supported(raw_value)
    
    def normalize(self, raw_value):
        if raw_value is None:
            return SingleValue(self.default, self)
        return self.field.normalize(raw_value)
    
    def get_dependencies(self, normalized_value):
        try:
            if normalized_value.values is None:
                return []
        except AttributeError:
            if normalized_value.value is None:
                return []
        
        return self.field.get_dependencies(normalized_value)
    
    def interpolate(self, normalized_value, values):
        try:
            if normalized_value.value is self.default:
                return self.default
        except AttributeError:
            pass
        
        return self.field.interpolate(normalized_value, values)
    
    def create_packed_value(self, normalized_value):
        # when we use default value but self.field is a list or dict
        # we know that we should use default value
        # if SingleValue is used by self.field then we should check
        # if given value is default
        try:
            if normalized_value.value is self.default:
                return self.default
        except AttributeError:
            pass
        
        return self.field.create_packed_value(normalized_value)
    
    def help(self, **kwargs):
        if "value" not in kwargs:
            kwargs["value"] = self.default
        self.field.help(**kwargs)
        return self
    
    def variant(self, **kwargs):
        self.field.variant(**kwargs)
        return self
    
    @property
    def _help(self):
        # FIXME: make _help private
        return self.field._help
