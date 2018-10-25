# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

class ConfigException(Exception):
    """Base exception for config errors."""
    pass

class ValidationError(ConfigException):
    """Exception for when there is error in validation of values in fields."""
    def __init__(self, message, *args):
        super(ValidationError, self).__init__(message, *args)
        self._partial_path = []

class PathValidationError(ConfigException):
    """Exception for improved readability - uses :class:`.ValidationError` to provide full path to field with error."""
    def __init__(self, validation_error):
        self.path = ".".join(repr(i) for i in validation_error._partial_path)
        super(PathValidationError, self).__init__(
            "%s: %s" % (self.path, validation_error)
        )

class CircularDependency(ConfigException):
    """Thrown when interpolation causes loop."""
    def __init__(self, *args, **kwargs):
        self.__cause__ = None # support for python2: raise Exception() from None
        super(CircularDependency, self).__init__(*args, **kwargs)
