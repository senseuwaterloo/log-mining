from dataclasses import dataclass
from functools import cached_property
from logs.templates import Template, Variable


@dataclass(slots=True, frozen=True)
class Parameter:
    event: "Event"
    position: int
    variable: Variable

    @property
    def value(self) -> str:
        return self.event.values[self.position]

    @value.setter
    def setvalue(self, value: str) -> None:
        self.event.values[self.position] = value


@dataclass(frozen=True)
class Event:
    id: int
    template: Template
    values: list[str]

    @cached_property
    def parameters(self):
        return [Parameter(self, i, v) for i, v in enumerate(v for v in self.template if isinstance(v, Variable))]

    @cached_property
    def text(self):
        def parts():
            i = 0
            for part in self.template:
                match part:
                    case str():
                        yield part
                    case Variable():
                        yield self.values[i]
                        i += 1
        return "".join(parts())

