# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

from contextlib import contextmanager

class BaseLoader(object):
    """Base class for any loader."""
    
    def __init__(self, filepath=None, fileobj=None):
        super(BaseLoader, self).__init__()
        
        self.filepath = filepath
        self.fileobj = fileobj
        
        self._setup()
    
    def _setup(self):
        """Extending classes can use it to setup loader."""
        pass
    
    @contextmanager
    def _source_stream(self):
        if self.filepath:
            with open(self.filepath, "rt") as f:
                yield f
        else:
            yield self.fileobj
    
    def _parse(self, data):
        """Extending classes should overwrite this method with parsing logic."""
        raise NotImplementedError()
    
    def load(self):
        """Reads source specified in constructor."""
        with self._source_stream() as f:
            return self._parse(f)

class YamlLoader(BaseLoader):
    """Reads yaml files."""
    
    def _setup(self):
        import yaml
        self._yaml = yaml
    
    def _parse(self, data):
        return self._yaml.safe_load(data)
