# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import logging
from glorpen.config.exceptions import ValidationError, CircularDependency, ConfigException
import os
import re
from collections import OrderedDict
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
    
class Dict(Field):
    """Converts values to :class:`collections.OrderedDict`
    
    Supports setting whole schema (specific keys and specific values)
    or just keys type and values type.
    
    Dict values are lazy resolved.
    """
    
    _schema = None
    _key_field = None
    _value_field = None
    
    def __init__(self, schema=None, keys=None, values=None, **kwargs):
        """
        To set specific schema pass dict to schema argument: ``{"param1": SomeField()}``.
        
        To specify keys and values type use keys and values arguments: ``Dict(keys=String(), values=Number())``. 
        """
        super(Dict, self).__init__(**kwargs)
        
        if schema is None:
            self._key_field = keys or String()
            self._value_field = values
        else:
            self._schema = schema
    
    def make_resolvable(self, r):
        if self._schema:
            r.on_resolve(self._check_keys_with_schema)
            r.on_resolve(self._normalize_with_schema)
        else:
            r.on_resolve(self._normalize)
    
    def _check_keys_with_schema(self, value, config):
        if value is None:
            value = {}
        
        spec_blanks = set()
        spec=set(self._schema.keys())
        val_keys = set(value.keys())
        
        for def_k, def_v in self._schema.items():
            try:
                if def_v.allow_blank or def_v.has_valid_default():
                    spec_blanks.add(def_k)
                    continue
            except AttributeError:
                spec_blanks.add(def_k)
                continue
        
        diff_new = val_keys.difference(spec)
        diff_missing = spec.difference(val_keys).difference(spec_blanks)
        if diff_new or diff_missing:
            msgs = []
            if diff_missing:
                msgs.append("missing keys %r" % diff_missing)
            if diff_new:
                msgs.append("excess keys %r" % diff_new)
            raise ValidationError("Found following errors: %s" % ", ".join(msgs))
        
        return value
    
    def _normalize_with_schema(self, value, config):
        ret = OrderedDict()
        for k,field in self._schema.items():
            with path_validation_error([k]):
                ret[k] = field.resolve(value.get(k))
        return ret
    
    def _normalize(self, value, config):
        ret = OrderedDict()
        
        if value is None:
            return ret
        
        for k,v in value.items():
            with path_validation_error(k):
                ret[self._key_field.resolve(k).resolve(config)] = self._value_field.resolve(v)
        
        return ret
    
    def is_value_supported(self, value):
        return value is None or isinstance(value, (dict,)) or super(Dict, self).is_value_supported(value)
    
class String(FieldWithDefault):
    """Converts value to string with optional interpolation."""
    
    re_part = re.compile(r'{{\s*([a-z._A-Z0-9]+)\s*}}')
    
    def resolve_parts(self, value, config):
        if value:
            def replace(matchobj):
                return config.get(matchobj.group(1))
            return self.re_part.sub(replace, value)
    
    def to_string(self, value, config):
        if value:
            try:
                return str(value)
            except Exception as e:
                raise ValidationError("Could not convert %r to string, got %r" % (value, e))
    
    def make_resolvable(self, r):
        r.on_resolve(self.to_string)
        r.on_resolve(self.resolve_parts)
    
    def is_value_supported(self, value):
        return isinstance(value, (str,)) or super(String, self).is_value_supported(value)

class Path(String):
    """Converts given value to disk path."""
    
    def to_path(self, value, config):
        return os.path.realpath(value)
    
    def make_resolvable(self, r):
        super(Path, self).make_resolvable(r)
        r.on_resolve(self.to_path)

class PathObj(Path):
    """Converts value to :class:`pathlib.Path` object"""
    def to_obj(self, value, config):
        import pathlib
        return pathlib.Path(value)
    
    def make_resolvable(self, r):
        super(PathObj, self).make_resolvable(r)
        r.on_resolve(self.to_obj)

class LogLevel(FieldWithDefault):
    """Converts log level name to internal number for use with :mod:`logging`"""
    
    _levels = None
    
    def _find_levels(self):
        if hasattr(logging, "_levelNames"):
            return dict((n,v) for n,v in logging._levelNames.items() if isinstance(v, int))
        if hasattr(logging, "_nameToLevel"):
            return logging._nameToLevel
        
        raise ConfigException("Could not find logging level names")
    
    def _get_levels(self):
        if self._levels is None:
            self._levels = self._find_levels()
        
        return self._levels
    
    def make_resolvable(self, r):
        r.on_resolve(self.to_level)
    
    def to_level(self, value, config):
        levels = self._get_levels()
        value = str(value).upper()
        
        if value in levels.keys():
            return levels[value]
        else:
            raise ValidationError("%r not in %r" % (value, levels.keys()))
    
    def is_value_supported(self, value):
        return isinstance(value, (str,)) or super(LogLevel, self).is_value_supported(value)

class List(FieldWithDefault):
    """Converts value to list.
    
    List values are lazy resolved.
    """
    
    def __init__(self, schema, **kwargs):
        super(List, self).__init__(**kwargs)
        
        self._values_field = schema
    
    def make_resolvable(self, r):
        r.on_resolve(self.normalize)
    
    def normalize(self, value, config):
        ret = []
        for i, v in enumerate(value):
            with path_validation_error(i):
                ret.append(self._values_field.resolve(v if v else None))
        return ret
    
    def is_value_supported(self, value):
        return isinstance(value, (tuple, list)) or super(List, self).is_value_supported(value)

class Variant(FieldWithDefault):
    """Converts value to normalized state using one :class:`.Field` choosen from multiple provided.
    
    To allow blank values you have to pass child field with enabled blank values.
    First field which supports value (:meth:`.Field.is_value_supported`) will be used to convert it.
    """
    def __init__(self, schema):
        allow_blank = False
        
        for s in schema:
            try:
                s_blank = s.allow_blank
            except AttributeError:
                continue
            
            if s_blank:
                allow_blank = True
                break
        
        super(Variant, self).__init__(allow_blank=allow_blank)
        
        self._values_fields = schema
    
    def make_resolvable(self, r):
        r.on_resolve(self.normalize)
    
    def normalize(self, value, config):
        for f in self._values_fields:
            if f.is_value_supported(value):
                return f.resolve(value, checked=True)
        
        raise ValidationError("Unsupported data %r" % (value,))
    
    def is_value_supported(self, value):
        if super(Variant, self).is_value_supported(value):
            return True
        
        for f in self._values_fields:
            if f.is_value_supported(value):
                return True
        return False

class Any(FieldWithDefault):
    """Field that accepts any value."""
    def is_value_supported(self, value):
        return True

class Number(FieldWithDefault):
    """Converts value to numbers."""
    #TODO: float, deciaml points
    def is_value_supported(self, value):
        try:
            int(value)
        except (ValueError, TypeError):
            return super(Number, self).is_value_supported(value)
        
        return True
    
    def make_resolvable(self, r):
        r.on_resolve(self._normalize)
    
    def _normalize(self, value, config):
        if value is not None:
            return int(value)
