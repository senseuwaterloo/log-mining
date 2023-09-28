from dataclasses import dataclass
from itertools import chain
from typing import Generator
from logs.templates import Template, TemplateBase, TemplateStatic, TemplateTree, TemplateVariable


@dataclass
class Parameter:
    event: "Event"
    variable: TemplateVariable

    @property
    def value(self) -> str:
        return self.event.values[self.variable.position]

    @value.setter
    def value(self, v: str):
        self.event.values[self.variable.position] = v


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
        return list(map(lambda v: Parameter(self, v), itervars(self.template)))

    @property
    def text(self):
        def stringify(node: TemplateTree | TemplateStatic | TemplateVariable) -> str:
            match node:
                case TemplateTree():
                    return "".join(map(stringify, node.parts))
                case TemplateStatic():
                    return str(node)
                case TemplateVariable():
                    return self.values[node.position]
        return stringify(self.template)
