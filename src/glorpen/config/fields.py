# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import logging
from glorpen.config.exceptions import ValidationError, CircularDependency, ConfigException
import os
import re

class ResolvableObject(object):
    """Configuration value ready to be resolved.
    
    Callbacks are registered by calling :attr:`.on_resolve`.
    
    To each callback are passed:
    
    * currently handled value
    
    * :class:`.Config` instance
    
    By using :class:`.Config` instance you can realize value based on any other value in configuration.
    If at any time resolver callback detects there is no value given in configuration file and we should use
    defaults given to :class:`.Field` it should raise :class:`.UseDefaultException`.
    
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
    
    def __init__(self, default=None, allow_blank=False):
        super(Field, self).__init__()
        self.default_value = default
        self.allow_blank = allow_blank
    
    def resolve(self, v):
        if not self.allow_blank and v is None:
            if self.has_valid_default():
                v = self.denormalize(self.default_value)
            else:
                raise ValidationError("Blank value is not allowed.")
        
        r = ResolvableObject(v)
        self.make_resolvable(r)
        return r
    
    def make_resolvable(self, r):
        pass
    
    def has_valid_default(self):
        if self.allow_blank:
            return True
        else:
            if self.default_value:
                return True
            else:
                return False
    
    def denormalize(self, value):
        raise NotImplementedError()

class Dict(Field):
    def __init__(self, **kwargs):
        super(Dict, self).__init__(default=kwargs)
    
    def make_resolvable(self, r):
        r.on_resolve(self.check_keys)
        r.on_resolve(self.normalize)
    
    def check_keys(self, v, config):
        spec_blanks = set()
        spec=set(self.default_value.keys())
        val_keys = set(v.keys())
        
        for def_k,def_v in self.default_value.items():
            if def_v.has_valid_default():
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
        
        return v
    
    def normalize(self, value, config):
        ret = {}
        for k,field in self.default_value.items():
            ret[k] = field.resolve(value.get(k) if value else None)
        return ret
    
    def denormalize(self, _dummy):
        #TODO: tests
        ret = {}
        for k,v in self.default_value.items():
            ret[k] = v.denormalize(v.default_value)
        return ret

class String(Field):
    
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
    
    def denormalize(self, value):
        return str(value)

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

class LogLevel(Field):
    
    _levels = None
    
    def _find_levels(self):
        if hasattr(logging, "_levelNames"):
            return dict((n,v) for n,v in logging._levelNames.items() if isinstance(v, int))
        if hasattr(logging, "_nameToLevel"):
            return logging._nameToLevel
        
        raise ConfigException("Could not find logging level names")
    
    def make_resolvable(self, r):
        r.on_resolve(self.to_level)
    
    def to_level(self, value, config):
        if self._levels is None:
            self._levels = self._find_levels()
        
        value = str(value).upper()
        
        if value in self._levels.keys():
            return self._levels[value]
        else:
            raise ValidationError("%r not in %r" % (value, self._levels.keys()))
