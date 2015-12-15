# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

class ConfigException(Exception):
    pass

class ValidationError(ConfigException):
    pass

class CircularDependency(ConfigException):
    def __init__(self, *args, **kwargs):
        self.__cause__ = None # support for python2: raise Exception() from None
        super(CircularDependency, self).__init__(*args, **kwargs)
