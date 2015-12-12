'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import unittest
from .fields import String, Path, LogLevel, Dict
from unittest.mock import Mock
import os
import logging
from .exceptions import ValidationError, CircularDependency
from . import Config

class FieldsTest(unittest.TestCase):

    def testString(self):
        c = Mock()
        
        f = String()
        ret = f.resolve("asd")
        
        self.assertEqual(ret.resolve(c), "asd")
        
        self.assertIsNone(f.resolve(None).resolve(c), "None when null")
        
        c.get.return_value = "qwe"
        f = String()
        ret = f.resolve("a{{something}}a")
        self.assertEqual(ret.resolve(c), "aqwea")
        c.get.assert_called_once_with("something")
    
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
