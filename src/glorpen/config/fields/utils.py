
def is_class_a_subclass(cls, class_or_tuple):
    return isinstance(cls, type) and issubclass(cls, class_or_tuple)
