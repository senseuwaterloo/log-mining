from abc import ABC, abstractmethod
from functools import cache
from re import Pattern
import re
from typing import Sequence

from logs.patterns import PatternStore

class TemplateBase(ABC):
    @abstractmethod
    def __str__(self) -> str:
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @property
    @abstractmethod
    def regex(self) -> str:
        ...


class TemplateTree(TemplateBase):
    parts: Sequence[TemplateBase]

    def __init__(self, *parts: TemplateBase):
        self.parts = parts

    def __str__(self):
        return "".join(map(str, self.parts))

    def __repr__(self):
        return "".join(map(repr, self.parts))

    @property
    @cache
    def regex(self):
        return "".join([str(p.regex) for p in self.parts])


class Template(TemplateTree):
    def __init__(self, *parts):
        super().__init__(*parts)
        
    def __repr__(self):
        return f"<template id={id(self)}>{super().__repr__()}</template>"


class TemplateStatic(TemplateBase):
    content: str

    def __init__(self, content: str):
        self.content = content

    def __str__(self):
        return self.content

    def __repr__(self):
        return str(self)

    @property
    def regex(self) -> str:
        return re.escape(self.content)


class TemplateVariable(TemplateBase):
    name: str
    type: str
    store : PatternStore

    def __init__(self, store: PatternStore, name: str, type: str):
        self.store = store
        self.name = name
        self.type = type

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"<var id={id(self)} name={self.name} type={self.type}>{self.regex}</var>"

    @property
    def regex(self):
        return self.store[self.type]
