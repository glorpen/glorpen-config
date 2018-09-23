# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import logging
from glorpen.config.exceptions import ValidationError, CircularDependency, ConfigException
import os
import re
from collections import OrderedDict

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
        self.callbacks.append(f)
    
    def resolve(self, config):
        if not hasattr(self, "_resolved_value"):
            self._resolved_value = self._do_resolve(config)
        
        return self._resolved_value
    
    def _do_resolve(self, config):
        
        if self._resolving:
            raise CircularDependency()
        
        v = self.o
        
        self._resolving = True
        for c in self.callbacks:
            v = c(v, config)
        self._resolving = False
        
        return v

class Field(object):
    """Single field in configuration file.
    
    Custom fields should register own resolvers/validators/normalizers by extending :attr:`.Field.make_resolvable`.
    
    For handling registered callbacks, see :class:`.ResolvableObject`.
    """
    
    def resolve(self, v, checked=False):
        if not checked:
            if not self.is_value_supported(v):
                raise ValidationError("Not supported value %r" % v)
        
        r = ResolvableObject(v)
        self.make_resolvable(r)
        return r
    
    def make_resolvable(self, r):
        pass
    
    def is_value_supported(self, value):
        return False

class _UnsetValue(): pass

class FieldWithDefault(Field):
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
    
    _schema = None
    _key_field = None
    _value_field = None
    
    def __init__(self, schema=None, keys=None, values=None, **kwargs):
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
            ret[k] = field.resolve(value.get(k))
        return ret
    
    def _normalize(self, value, config):
        ret = OrderedDict()
        
        if value is None:
            return ret
        
        for k,v in value.items():
            ret[self._key_field.resolve(k).resolve(config)] = self._value_field.resolve(v)
        
        return ret
    
    def is_value_supported(self, value):
        return value is None or isinstance(value, (dict,)) or super(Dict, self).is_value_supported(value)
    
class String(FieldWithDefault):
    
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
    
    def to_path(self, value, config):
        return os.path.realpath(value)
    
    def make_resolvable(self, r):
        super(Path, self).make_resolvable(r)
        r.on_resolve(self.to_path)

class PathObj(Path):
    """Path as pathlib.Path object"""
    def to_obj(self, value, config):
        import pathlib
        return pathlib.Path(value)
    
    def make_resolvable(self, r):
        super(PathObj, self).make_resolvable(r)
        r.on_resolve(self.to_obj)

class LogLevel(FieldWithDefault):
    
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
    def __init__(self, schema, **kwargs):
        super(List, self).__init__(**kwargs)
        
        self._values_field = schema
    
    def make_resolvable(self, r):
        r.on_resolve(self.normalize)
    
    def normalize(self, value, config):
        ret = []
        for v in value:
            ret.append(self._values_field.resolve(v if v else None))
        return ret
    
    def is_value_supported(self, value):
        return isinstance(value, (tuple, list)) or super(List, self).is_value_supported(value)

class Variant(FieldWithDefault):
    def __init__(self, schema, **kwargs):
        super(Variant, self).__init__(**kwargs)
        
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
    def is_value_supported(self, value):
        return True
