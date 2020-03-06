import contextlib

class BaseHelp(object):
    has_description = False

    def __init__(self, **kwargs):
        super().__init__()

        self.set(**kwargs)

    def set(self, **kwargs):
        for k,v in kwargs.items():
            getattr(self, "set_" + k)(v)
        return self

    def set_description(self, v):
        self.description = v
        self.has_description = True

    has_value = False
    
    def set_value(self, v):
        self.value = v
        self.has_value = True

class HelpVariant(BaseHelp):
    pass

class Help(object):
    has_variants = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.variants = []
    
    def set(self, **kwargs):
        self.variants.append(HelpVariant(**kwargs))
        self.has_variants = True
        return self

class ContainerHelp(BaseHelp):
    are_children_list = False
    are_children_hash = False
    are_children_alts = False

    children = None

    # [] => list
    # {} => dict
    # a,b,c => options (eg.Variant field)
    def set_children(self, *args):
        
        if isinstance(args[0], dict):
            self.are_children_hash = True
            self.children = args[0]
        elif isinstance(args[0], (tuple, list)):
            self.are_children_list = True
            self.children = args[0]
        else:
            self.are_children_alts = True
            self.children = args

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
            if hasattr(help, "variants"):
                with visitor(self, "node.variants", help):
                    for variant in help.variants:
                        with visitor(self, "variant", variant, help):
                            pass
            if hasattr(help, "children"):
                with visitor(self, "container", help):
                    if help.are_children_hash:
                        with visitor(self, "container.hash", help):
                            for k,v in help.children.items():
                                with visitor(self, "item.hash", k, v):
                                    self.visit(v)
                    elif help.are_children_list:
                        with visitor(self, "container.list", help):
                            for v in help.children:
                                with visitor(self, "item.list", v):
                                    self.visit(v)
                    else:
                        with visitor(self, "container.alternative", help):
                            for v in help.children:
                                with visitor(self, "item.alternative", v):
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
