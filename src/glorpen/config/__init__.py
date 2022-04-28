import dataclasses

from glorpen.config.config import Config
from glorpen.config.fields.simple import UnionType, SimpleTypes, SequenceTypes


def default():
    c = Config()
    c.register(UnionType)
    c.register(SimpleTypes)
    c.register(SequenceTypes)

    return c

