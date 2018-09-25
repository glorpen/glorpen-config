# -*- coding: utf-8 -*-
'''
Created on 8 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
from glorpen.config.fields import ResolvableObject
from glorpen.config.exceptions import CircularDependency
from collections import OrderedDict
from glorpen.config import exceptions
import contextlib

__all__ = ["Config", "__version__"]

__version__ = "1.0.1"

@contextlib.contextmanager
def readable_validation_error(resolve_path):
    try:
        yield
    except exceptions.ValidationError as e:
        full_path = resolve_path + e._partial_path
        raise exceptions.PathValidationError(e, ".".join(repr(i) for i in full_path)) from e

class Config(object):
    
    data = None
    
    def __init__(self, spec, loader, split_character='.'):
        super(Config, self).__init__()
        
        self.loader = loader
        self.spec = spec
        self.split_character = split_character
    
    def finalize(self, data=None):
        """Load and resolve configuration in one go.
        
        If data argument is given loader specified in constructor will not be used.
        """
        
        if data:
            self.load_data(data)
        else:
            self.load()
        self.resolve()
        return self
    
    def load(self):
        self.load_data(self.loader.load())
    
    def load_data(self, data):
        """Loads given data as source."""
        self.data = self.spec.resolve(data)
    
    def _get_value(self, data, resolve_path=None):
        if isinstance(data, ResolvableObject):
            return self._visit_all(data.resolve(self), resolve_path)
        else:
            return data
    
    def _visit_all(self, data, resolve_path=None):
        
        if not resolve_path:
            resolve_path = []
        
        if isinstance(data, dict):
            ret = OrderedDict()
            for k,v in data.items():
                my_path = resolve_path + [k]
                with readable_validation_error(my_path):
                    ret[k] = self._visit_all(v, my_path)
            
            return ret
        
        if isinstance(data, list):
            return [self._visit_all(v, resolve_path + [i]) for i,v in enumerate(data)]
        
        return self._get_value(data, resolve_path)
    
    def resolve(self):
        """Visits all values and converts them to normalized form."""
        self.data = self.data.resolve(self)
        self.data = self._visit_all(self.data)
    
    def get(self, p):
        """Gets value from config. To get value under `some_key` use dotted notation: `some_key.value` (defaults)."""
        d = self.data
        
        if isinstance(p, str):
            parts = p.split(self.split_character)
        else:
            parts = p
        
        try:
            for i in parts:
                d = self._get_value(d)
                if not i in d:
                    raise ValueError("No key %r in path %r" % (i, p))
                d = d.get(i)
            return self._get_value(d)
        except CircularDependency:
            raise CircularDependency("Circular dependency at %r" % p)
