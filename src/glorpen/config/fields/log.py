# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import logging
from glorpen.config.exceptions import ValidationError, ConfigException
from glorpen.config.fields.base import FieldWithDefault

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
