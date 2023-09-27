from dataclasses import dataclass
from itertools import chain
from typing import Any, Generator, Iterator, Sequence
from logs.templates import Template, TemplateBase, TemplateTree, TemplateVariable

@dataclass
class Parameter:
    variable: TemplateVariable
    value: str

@dataclass
class Event:
    id: int
    template: Template
    values: Sequence[str]

    @property
    def parameters(self):
        def itervars(node: TemplateBase) -> Generator[TemplateVariable, None, None]:
            match node:
                case TemplateTree():
                    yield from chain(*map(itervars, node.parts))
                    return
                case TemplateVariable():
                    yield node
                    return
                case _:
                    return
        return list(map(lambda v: Parameter(*v), zip(itervars(self.template), self.values)))
