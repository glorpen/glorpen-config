'''
Created on 8 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import os
import sys
import logging
import re
import functools
import yaml

from .fields import ResolvableObject
from .exceptions import CircularDependency

__all__ = ["Config"]

class Config(object):
    
    data = None
    
    def __init__(self, path, spec):
        super(Config, self).__init__()
        
        self.path = path
        self.spec = spec
    
    def finalize(self):
        self.load()
        self.resolve()
        return self
    
    def load(self):
        with open(self.path, "rt") as f:
            self.data = self.spec.resolve(next(yaml.safe_load_all(f)))
    
    def _get_value(self, data):
        if isinstance(data, ResolvableObject):
            return self._visit_all(data.resolve(self))
        else:
            return data
    
    def _visit_all(self, data):
        
        if isinstance(data, dict):
            return dict([k, self._visit_all(v)] for k,v in data.items())
        
        if isinstance(data, list):
            return [self._visit_all(i) for i in data]
        
        return self._get_value(data)
    
    def resolve(self):
        self.data = self.data.resolve(self)
        self.data = self._visit_all(self.data)
    
    def get(self, p):
        d = self.data
        
        if isinstance(p, str):
            parts = p.split(".")
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
            raise CircularDependency("Circular dependency at %r" % p) from None
