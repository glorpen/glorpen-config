'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

class ConfigException(Exception):
    pass

class ValidationError(ConfigException):
    pass

class UseDefaultException(ConfigException):
    pass

class CircularDependency(ConfigException):
    pass
