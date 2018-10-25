# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

class ConfigException(Exception):
    pass

class ValidationError(ConfigException):
    def __init__(self, message, *args):
        super(ValidationError, self).__init__(message, *args)
        self._partial_path = []

class PathValidationError(ConfigException):
    def __init__(self, validation_error):
        self.path = ".".join(repr(i) for i in validation_error._partial_path)
        super(PathValidationError, self).__init__(
            "%s: %s" % (self.path, validation_error)
        )

class CircularDependency(ConfigException):
    def __init__(self, *args, **kwargs):
        self.__cause__ = None # support for python2: raise Exception() from None
        super(CircularDependency, self).__init__(*args, **kwargs)
