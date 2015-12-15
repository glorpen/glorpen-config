# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import unittest
from glorpen.config.fields import String, Path, LogLevel, Dict
import os
import logging
from glorpen.config.exceptions import ValidationError, CircularDependency
from glorpen.config import Config

try:
    from unittest.mock import Mock
except ImportError:
    #support for python2
    from mock import Mock

class FieldsTest(unittest.TestCase):

    def testString(self):
        c = Mock()
        
        f = String(allow_blank=True)
        ret = f.resolve("asd")
        
        self.assertEqual(ret.resolve(c), "asd")
        
        self.assertIsNone(f.resolve(None).resolve(c), "None when null")
        
        c.get.return_value = "qwe"
        f = String()
        ret = f.resolve("a{{something}}a")
        self.assertEqual(ret.resolve(c), "aqwea")
        c.get.assert_called_once_with("something")
    
    def testStringDefaultInterpolation(self):
        c = Config(spec=Dict(
            a=String(default="letter a"),
            aa=String(default="a {{a}}")
        ))
        c.load_data({})
        c.resolve()
        
        self.assertEqual(c.get("aa"), "a letter a")
    
    def testPath(self):
        c = Mock()
        f = Path()
        ret = f.resolve(__file__+"/..")
        
        self.assertEqual(ret.resolve(c), os.path.dirname(__file__))
    
    def testLogLevel(self):
        c = Mock()
        f = LogLevel()
        self.assertEqual(f.resolve("WARNING").resolve(c), logging.WARNING)
        
        with self.assertRaises(ValidationError):
            f.resolve("asdasd").resolve(c)

class ConfigTest(unittest.TestCase):
    def testCircularDependency(self):
        c = Config(spec=Dict(a=String()))
        c.load_data({"a":"a{{a}}a"})
        
        with self.assertRaises(CircularDependency):
            c.resolve()

if __name__ == "__main__":
    unittest.main()
