# -*- coding: utf-8 -*-
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

from glorpen.config.fields import ResolvableObject
from glorpen.config.exceptions import CircularDependency
from contextlib import contextmanager

__all__ = ["Config", "__version__"]

__version__ = "1.0.1"

class Config(object):
    
    data = None
    
    def __init__(self, spec, filepath=None, fileobj=None):
        super(Config, self).__init__()
        
        self.filepath = filepath
        self.fileobj = fileobj
        self.spec = spec
    
    def finalize(self, data=None):
        """Load and resolve configuration in one go.
        
        If data argument is given source specified in constructor will not be read.
        """
        
        if data:
            self.load_data(data)
        else:
            self.load()
        self.resolve()
        return self
    
    @contextmanager
    def _source_stream(self):
        if self.filepath:
            with open(self.filepath, "rt") as f:
                yield f
        else:
            yield self.fileobj
    
    def load(self):
        """Reads source specified in constructor."""
        with self._source_stream() as f:
            self.load_data(next(yaml.safe_load_all(f)))
    
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
            return dict([k, self._visit_all(v)] for k,v in data.items())
        
        if isinstance(data, list):
            return [self._visit_all(i) for i in data]
        
        return self._get_value(data)
    
    def resolve(self):
        """Visits all values and converts them to normalized form."""
        self.data = self.data.resolve(self)
        self.data = self._visit_all(self.data)
    
    def get(self, p):
        """Gets value from config. To get value under `some_key` use dotted notation: `some_key.value`."""
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
            raise CircularDependency("Circular dependency at %r" % p)
