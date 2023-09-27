from dataclasses import dataclass
from itertools import chain
from typing import Generator
from logs.templates import Template, TemplateBase, TemplateTree, TemplateVariable


@dataclass
class Parameter:
    event: "Event"
    index: int
    variable: TemplateVariable

    @property
    def value(self):
        return self.event.values[self.index]

    @value.setter
    def setvalue(self, value):
        self.event.values[self.index] = value


@dataclass
class Event:
    id: int
    template: Template
    values: list[str]

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
        return list(map(lambda v: Parameter(self, *v), enumerate(itervars(self.template))))
