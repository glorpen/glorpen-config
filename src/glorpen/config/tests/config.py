import unittest
import pathlib

from glorpen.config.fields.base import Field
from glorpen.config.fields.simple import Dict, Number
from glorpen.config.config import Config
from glorpen.config import exceptions

class MockField(Field):
    pass

class ConfigTest(unittest.TestCase):
    def test_resolving_unknown_dependency(self):
        c = Config(MockField())
        path = ('a','b')
        with self.assertRaisesRegex(Exception, f"{repr(path)}"):
            c._resolve_dependencies({}, {path: []})
    
    def test_not_supported_value_path(self):
        c = Config(Dict({"a":Dict({"b":Dict({"c":Number()})})}))
        with self.assertRaisesRegex(exceptions.TraceableConfigException, "'a'.'b'"):
            c.get({"a":{"b":{"c":"xx"}}})
