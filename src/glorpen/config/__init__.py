import contextlib

from glorpen.config.model.transformer import Transformer
from glorpen.config.model.schema import Schema
from glorpen.config.validation import Validator


@contextlib.contextmanager
def _try_import():
    try:
        yield
    except ImportError:
        return


def default(schema: Schema = None, validator: Validator = None):
    c = Transformer(schema or Schema(), validator or Validator())

    from glorpen.config.fields.simple import UnionType, SimpleTypes, CollectionTypes, BooleanType, PathType, LiteralType

    c.register_type(UnionType)
    c.register_type(SimpleTypes)
    c.register_type(CollectionTypes)
    c.register_type(BooleanType)
    c.register_type(PathType)
    c.register_type(LiteralType)

    with _try_import():
        from glorpen.config.fields.version import VersionType
        c.register_type(VersionType)

    with _try_import():
        from glorpen.config.fields.version import VersionType
        c.register_type(VersionType)

    with _try_import():
        from glorpen.config.fields.log import LogLevelType
        c.register_type(LogLevelType)

    return c
