import contextlib

class Help(object):
    has_value = False
    has_description = False
    has_children = False
    has_variants = False

    def __init__(self, **kwargs):
        super().__init__()

        self.variants = []

        self.set(**kwargs)

    def set(self, **kwargs):
        for k,v in kwargs.items():
            getattr(self, "set_" + k)(v)
        return self
    
    def variant(self, **kwargs):
        self.variants.append(self.__class__(**kwargs))
        self.has_variants = True
        return self

    def set_description(self, v):
        self.description = v
        self.has_description = True
    
    def set_value(self, v):
        self.value = v
        self.has_value = True
    
    def set_children(self, v):
        self.children = v
        self.has_children = True

@contextlib.contextmanager
def visitor(self, tag, *args):
    names = [("any", (tag,)), (tag.replace(".", "_"), tuple())]

    for n, arg in names:
        method = "visit_" + n
        if hasattr(self, method):
            getattr(self, method)(*(arg + args))
    
    yield

    for n, arg in names:
        method = "leave_" + n
        if hasattr(self, method):
            getattr(self, method)(*(arg + args))

class Renderer(object):
    def visit(self, help):
        with visitor(self, "node", help):
            if help.has_variants:
                for variant in help.variants:
                    with visitor(self, "variant", variant):
                        pass
            if help.has_children:
                with visitor(self, "container", help):
                    if isinstance(help.children, (dict,)):
                        with visitor(self, "container.hash", help):
                            for k,v in help.children.items():
                                with visitor(self, "item.hash", k, v):
                                    self.visit(v)
                    else:
                        with visitor(self, "container.list", help):
                            for v in help.children:
                                with visitor(self, "item.list", v):
                                    self.visit(v)

    def reset(self):
        raise NotImplementedError()

    def finish(self):
        raise NotImplementedError()

    def render(self, help):
        self.reset()
        self.visit(help)
        return self.finish()

class Reader(object):
    def read(self):
        raise NotImplementedError()

class Translator(object):
    def __init__(self, config):
        super().__init__()

        self.config = config
        
    def read(self, reader: Reader):
        return self.config.get(reader.read())

    def generate_example(self, renderer: Renderer):
        h = self.config.help()
        return renderer.render(h)

    def write_example(self, renderer: Renderer, path):
        with open(path, "wt") as f:
            f.write(self.generate_example(renderer))
