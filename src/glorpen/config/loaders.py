'''
Created on 22 wrz 2018

@author: glorpen
'''
from contextlib import contextmanager

class BaseLoader(object):
    def __init__(self, filepath=None, fileobj=None):
        super(BaseLoader, self).__init__()
        
        self._setup()
    
    def _setup(self):
        pass
    
    @contextmanager
    def _source_stream(self):
        if self.filepath:
            with open(self.filepath, "rt") as f:
                yield f
        else:
            yield self.fileobj
    
    def _parse(self, data):
        raise NotImplementedError()
    
    def load(self):
        """Reads source specified in constructor."""
        with self._source_stream() as f:
            return self._parse(f)

class YamlLoader(BaseLoader):
    def _setup(self):
        import yaml
        self._yaml = yaml
    
    def _parse(self, data):
        return self._yaml.safe_load(data)
