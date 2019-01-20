# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
from glorpen.config.exceptions import ValidationError, CircularDependency
import contextlib

def _as_list(v):
    """Returns given object wrapped in list if not already"""
    if not isinstance(v, (list)):
        return [v]
    return v

@contextlib.contextmanager
def path_validation_error(after=None, before=None):
    """Adds given path to validation error to make exceptions easy to read"""
    if after:
        after = _as_list(after)
    
    if before:
        before = _as_list(before)
    
    try:
        yield
    except ValidationError as e:
        
        if not hasattr(e, "_partial_path"):
            e._partial_path = []
        
        if after:
            e._partial_path.extend(after)
        
        if before:
            e._partial_path = before + e._partial_path
        
        raise e

def resolve(obj, config):
    """Returns real object value (resolved) if applicable"""
    if isinstance(obj, ResolvableObject):
        return obj.resolve(config)
    return obj

class ResolvableObject(object):
    """Configuration value ready to be resolved.
    
    Callbacks are registered by calling :attr:`.on_resolve`.
    
    To each callback are passed:
    
    * currently handled value
    
    * :class:`.Config` instance
    
    By using :class:`.Config` instance you can realize value based on any other value in configuration.
    
    If value is invalid, callback should raise :class:`.ValidationError` with appropriate error message.
    """
    
    _resolving = False
    
    def __init__(self, o):
        super(ResolvableObject, self).__init__()
        self.o = o
        self.callbacks = []
    
    def on_resolve(self, f):
        """Registers given callback to run when resolving values.
        Passed function should accept following arguments:
        
        - value - may be a value or :class:`.ResolvableObject`
        - a :class:`.Config` instance
        """
        self.callbacks.append(f)
    
    def resolve(self, config):
        """Resolves value with given config"""
        if not hasattr(self, "_resolved_value"):
            self._resolved_value = self._do_resolve(config)
        
        return self._resolved_value
    
    def _do_resolve(self, config):
        
        if self._resolving:
            raise CircularDependency()
        
        v = self.o
        
        self._resolving = True
        for c in self.callbacks:
            v = resolve(c(v, config), config)
        self._resolving = False
        
        return v

class Field(object):
    """Single field in configuration file.
    
    Custom fields should register own resolvers/validators/normalizers by extending :meth:`.make_resolvable`.
    
    For handling registered callbacks, see :class:`.ResolvableObject`.
    """
    
    def resolve(self, v, checked=False):
        """Wraps value in :class:`.ResolvableObject` optionally checking whether provided value is supported."""
        if not checked:
            if not self.is_value_supported(v):
                raise ValidationError("Not supported value %r" % v)
        
        r = ResolvableObject(v)
        self.make_resolvable(r)
        return r
    
    def make_resolvable(self, r):
        """Used to register normalizes in current :class:`.ResolvableObject`."""
        pass
    
    def is_value_supported(self, value):
        """Checks if provided value is supported by this field"""
        return False

class _UnsetValue(): pass

class FieldWithDefault(Field):
    """Base class for nullable fields with defaults."""
    
    def __init__(self, default=_UnsetValue, allow_blank=False):
        super(FieldWithDefault, self).__init__()
        self.default_value = default
        self.allow_blank = allow_blank
    
    def has_valid_default(self):
        return self.default_value is not _UnsetValue
    
    def resolve(self, v, **kwargs):
        if not self.allow_blank and v is None:
            if self.has_valid_default():
                v = self.default_value
            else:
                raise ValidationError("Blank value is not allowed.")
        
        return super(FieldWithDefault, self).resolve(v, **kwargs)
    
    def is_value_supported(self, value):
        return value is None
