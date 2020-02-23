# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
# from glorpen.config.fields import path_validation_error
from collections import OrderedDict
from glorpen.config import exceptions

__all__ = ["Config", "__version__"]

__version__ = "3.0.0"


class Config(object):
    """Config validator and normalizer."""
    
    def walk(self, normalized_tree, path=[]):
        if hasattr(normalized_tree, "values"):
            for k,v in normalized_tree.values.items():
                lpath = tuple(list(path) + [k])
                yield from self.walk(v, lpath)
                yield lpath, v
    
    def __init__(self, spec, loader=None):
        super(Config, self).__init__()
        
        self.loader = loader
        self.spec = spec
    
    def get(self, raw_value):
        # raw_value = self.loader.load()
        if not self.spec.is_value_supported(raw_value):
            raise Exception("value is not supported")
        
        normalized_value = self.spec.normalize(raw_value)
        index, required_deps_by_path = self._find_dependencies(normalized_value)
        resolved_paths = self._resolve_dependencies(index, required_deps_by_path)

        self._inject_resolved_dependencies(resolved_paths, normalized_value)

        packed_tree = self.spec.pack(normalized_value)
        self._validate(index, packed_tree)

        return packed_tree

    def _find_dependencies(self, normalized_value):
        index = {}
        required_deps_by_path = {}

        for path, i in self.walk(normalized_value):
            index[path] = i
            deps = i.field.get_dependencies(i)
            if deps:
                required_deps_by_path[path] = deps
        
        return index, required_deps_by_path

    def _resolve_dependencies(self, index, required_deps_by_path):
        resolved_paths = {}
        something_was_done = True
        
        while something_was_done:
            something_was_done = False
            for req_path, req_deps in required_deps_by_path.items():
                if req_path in resolved_paths:
                    continue
                
                unknown_deps = set(req_deps).intersection(set(required_deps_by_path).difference(resolved_paths))
                if unknown_deps:
                    print("deps for dep - skipping")
                    continue
                
                something_was_done = True

                values = []
                for i in req_deps:
                    values.append(resolved_paths[i] if i in resolved_paths else index[i].value)
                resolved_paths[req_path] = index[req_path].field.interpolate(index[req_path], values)

        unsolvable_deps = set(required_deps_by_path).difference(resolved_paths)
        if unsolvable_deps:
            raise Exception("Paths could not be solved: %r", unsolvable_deps)
        
        return resolved_paths
    
    def _inject_resolved_dependencies(self, resolved_paths, normalized_value):
        for path, value in resolved_paths.items():
            i = normalized_value
            for p in path:
                i = normalized_value.values[p]
            i.value = value
    
    def _validate(self, index, packed_tree):
        errors = {}
        for path, f in index.items():
            try:
                f.field.validate(f.packed, packed_tree)
            except Exception as e:
                errors[path] = e

        if errors:
            raise Exception(errors)
