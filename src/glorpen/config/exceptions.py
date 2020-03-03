# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

import contextlib

@contextlib.contextmanager
def path_error(key):
    try:
        yield
    except ConfigException as e:
        if not hasattr(e, "config_path"):
            e.config_path = []
        e.config_path.insert(0, key)
        raise e

class ConfigException(Exception):
    """Base exception for config errors."""
    pass

class TraceableConfigException(ConfigException):
    """Exception for improved readability - uses :class:`.ValidationError` to provide full path to field with error."""
    def __init__(self, exception):
        self.path = ".".join(repr(i) for i in exception.config_path)
        self.__cause__ = exception
        super(TraceableConfigException, self).__init__(
            "At path %s: %s" % (self.path, exception)
        )
