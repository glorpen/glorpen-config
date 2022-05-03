import dataclasses
import typing

from glorpen.config.model.schema import Schema


@dataclasses.dataclass
class Dummy2:
    a_field: str


@dataclasses.dataclass
class Dummy:
    """class doc"""

    a_field: typing.Union[str, Dummy2] = dataclasses.field(metadata={"doc": "field doc", "opt1": 1})


def test_docs():
    p = Schema().normalize(Dummy)
    assert p.doc == "class doc"
    assert p.args["a_field"].doc == "field doc"


def test_options_are_inherited_only_by_types():
    p = Schema().normalize(Dummy)
    assert p.args['a_field'].args[1].args["a_field"].options == {}
