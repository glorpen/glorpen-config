import unittest
import pathlib

from glorpen.config.fields.simple import String, Reference, Path, PathObj, Any, Dict, Variant, Number
from glorpen.config.fields.base import SingleValue

class StringTest(unittest.TestCase):
    def create_with_value(self, s):
        f = String(left_char="<", right_char=">", split_by=":")
        return SingleValue(s, f)

    def test_dependencies_parsing(self):
        v = self.create_with_value("example")
        self.assertFalse(v.field.get_dependencies(v), "No deps found")

        v = self.create_with_value("ex<d>")
        self.assertEqual(v.field.get_dependencies(v), (('d',),), "Single, simple dependency")

        v = self.create_with_value("examp<a:b:c>le")
        self.assertEqual(v.field.get_dependencies(v), (('a','b','c'),), "Deep dependency")

        v = self.create_with_value("examp<a[5]:c>le")
        self.assertEqual(v.field.get_dependencies(v), (('a',5,'c'),), "Dependency with number")

        v = self.create_with_value("examp<[5]:c>le")
        self.assertEqual(v.field.get_dependencies(v), ((5,'c'),), "Dependency starting with number")
    
    def test_interpolation(self):
        v = self.create_with_value("t<noop>t")
        iv = v.field.interpolate(v, ["xx"])

        self.assertEqual(iv, "txxt")
    
    def test_interpolation_with_non_string(self):
        v = self.create_with_value("t<noop>t")
        iv = v.field.interpolate(v, [1])
        self.assertEqual(iv, "t1t")


class ReferenceTest(unittest.TestCase):
    def test_value(self):
        f = Reference()
        v = SingleValue("ext-id", f)
        
        self.assertEqual(f.get_dependencies(v.value), ("ext-id",))
        iv = f.interpolate(v, ["some-value"])
        self.assertEqual(iv, "some-value")

class PathTest(unittest.TestCase):
    def test_value(self):
        f = Path()
        v = f.normalize(__file__ + "/asd/..")

        self.assertEqual(v.value, __file__, "Path is resolved by realpath")

class PathObjTest(unittest.TestCase):
    def test_value(self):
        v = PathObj().normalize(__file__).value
        self.assertIsInstance(v, pathlib.Path)

class AnyTest(unittest.TestCase):
    def test_value(self):
        f = Any()
        v = f.normalize(self)
        self.assertIs(f.pack(v), self)

class DictTest(unittest.TestCase):
    def test_value_with_key_and_value_fields(self):
        f = Dict(keys=String(), values=String())
        v = f.normalize({'a':1})
        self.assertEqual(f.pack(v), {'a':'1'})

    def test_value_with_schema(self):
        f = Dict({'a': String()})
        v = f.normalize({'a':'1'})
        self.assertEqual(f.pack(v), {'a':'1'})
    
    def test_key_interpolation(self):
        f = Dict(keys=String(), values=Any())
        v = f.normalize({'a{x}{x}':'1', 'b{x}{x}':'x'})
        f.interpolate(v, ['1', '2', '3', '4'])
        result = f.pack(v)

        self.assertIn("a12", result, "First key was interpolated")
        self.assertIn("b34", result, "Second key was interpolated")


class VariantTest(unittest.TestCase):
    def test_value_switching(self):
        f = Variant([Number(), String()])
        self.assertEqual(f.pack(f.normalize("1")), 1, "As number")
        self.assertEqual(f.pack(f.normalize("1a")), "1a", "As string")
