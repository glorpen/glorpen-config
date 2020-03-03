'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import contextlib
from collections import OrderedDict
from glorpen.config import exceptions
from glorpen.config.translators.base import Help

class Value(object):
    packed = None

    def __init__(self, field):
        super().__init__()

        if not isinstance(field, (Field,)):
            raise exceptions.ConfigException("Value %r passed as field is not a field" % field)
        
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

    # used by Optional wrapper
    default_value = None

    def __init__(self, validators=None):
        super().__init__()
        self._validators = list(validators) if validators else []
        self.help_config = Help()

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
        self.help_config.set(**kwargs)
        return self
    
    def variant(self, **kwargs):
        self.help_config.variant(**kwargs)
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

        self.help_config.set(value=self.default)
    
    def is_value_supported(self, raw_value):
        return raw_value is None or self.field.is_value_supported(raw_value)
    
    def normalize(self, raw_value):
        if raw_value is None:
            return SingleValue(Unset, self)
        return self.field.normalize(raw_value)
    
    def get_dependencies(self, normalized_value):
        try:
            if normalized_value.value is Unset:
                return []
        except AttributeError:
            pass
        
        return self.field.get_dependencies(normalized_value)
    
    def interpolate(self, normalized_value, values):
        self.field.interpolate(normalized_value, values)
    
    def create_packed_value(self, normalized_value):
        # when we use default value but self.field is a list or dict
        # we know that we should use default value
        # if SingleValue is used by self.field then we should check
        # if given value is default
        try:
            if normalized_value.value is Unset:
                return self.default
        except AttributeError:
            pass
        
        return self.field.create_packed_value(normalized_value)

def is_optional(field):
    return isinstance(field, Optional)
