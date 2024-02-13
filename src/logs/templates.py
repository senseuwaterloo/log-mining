from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from re import Pattern
import re
from typing import Callable, Iterator, Sequence, Union, cast

from logs.patterns import PatternStore, UndefinedPatternType

class TemplatePart(ABC):
    @abstractmethod
    def __str__(self) -> str:
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def __hash__(self) -> int:
        ...

    @abstractmethod
    def __eq__(self, other) -> bool:
        ...


@dataclass(eq=True, frozen=True)
class TemplateStatic(TemplatePart):
    content: str

    def __str__(self):
        return self.content

    def __repr__(self):
        return str(self)


@dataclass(eq=True, )
class TemplateVariable(TemplatePart):
    type: str

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"<var type={self.type}/>"


type Tree[A] = A | list[Tree[A]]

def treecata[A, B](f: Callable[[A], B], g: Callable[[list[B]], B], tree: Tree[A]) -> B:
    if not isinstance(tree, list):
        return f(tree)
    return g([treecata(f, g, t) for t in tree])

def treeiter[A](tree: Tree[A]) -> Iterator[A]:
    if isinstance(tree, list):
        for t in tree:
            yield from treeiter(t)
    yield cast(A, tree)

@dataclass(eq=True, frozen=True)
class Template:
    tree: Tree[TemplatePart]

    def __repr__(self) -> str:
        return f"<template>{treecata(repr, "".join, self.tree)}</template>"

    def __iter__(self) -> Iterator[TemplatePart]:
        yield from treeiter(self.tree)

