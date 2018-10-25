# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
from glorpen.config.fields import ResolvableObject, path_validation_error
from glorpen.config.exceptions import CircularDependency
from collections import OrderedDict
from glorpen.config import exceptions
from six import raise_from

__all__ = ["Config", "__version__"]

__version__ = "2.0.0"

class Config(object):
    """Config validator and normalizer."""
    
    data = None
    
    def __init__(self, spec, loader=None, split_character='.'):
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
    
    def _get_value(self, data):
        if isinstance(data, ResolvableObject):
            return self._visit_all(data.resolve(self))
        else:
            return data
    
    def _visit_all(self, data):
        if isinstance(data, dict):
            ret = OrderedDict()
            for k,v in data.items():
                with path_validation_error(before=k):
                    ret[k] = self._visit_all(v)
            
            return ret
        
        if isinstance(data, list):
            ret = []
            
            for i,v in enumerate(data):
                with path_validation_error(before=i):
                    ret.append(self._visit_all(v)) 
            
            return ret
        
        return self._get_value(data)
    
    def resolve(self):
        """Visits all values and converts them to normalized form."""
        self.data = self.data.resolve(self)
        try:
            self.data = self._visit_all(self.data)
        except exceptions.ValidationError as e:
            raise_from(exceptions.PathValidationError(e), None)
    
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
