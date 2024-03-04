from dataclasses import dataclass
from typing import Callable, Iterator, Union
from lxml import etree
from functools import cached_property

import re


DEFAULT_VARIABLE_PATTERN = r".*"


@dataclass(eq=True, frozen=True)
class Variable:
    pattern: str

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.pattern == DEFAULT_VARIABLE_PATTERN:
            return "<var/>"
        return f'<var pattern="{self.pattern}"/>'


type TemplatePart = str | Variable


@dataclass(eq=True, frozen=True)
class Template:
    _tree: list[Union[str, TemplatePart, "Template"]]

    @staticmethod
    def from_xml(string: str):
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(string, parser=parser)

        def iter_etree(e):
            yield e.text or ""
            for child in e:
                yield from_etree(child)
                yield child.tail or ""

        def from_etree(e):
            match e.tag:
                case "template":
                    return Template(list(iter_etree(e)))
                case "var":
                    return Variable(e.get("pattern") or DEFAULT_VARIABLE_PATTERN)

        template = from_etree(root)
        if not isinstance(template, Template):
            raise RuntimeError("input is not a valid template string")
        return template

    @cached_property
    def regex(self) -> re.Pattern:
        parts = []
        for part in self:
            match part:
                case str():
                    parts.append(re.escape(part))
                case Variable(pattern):
                    parts.append("(" + pattern + ")")
        return re.compile("".join(parts))

    def cata[A](self, f: Callable[[list[Union[TemplatePart, A]]], A]) -> A:
        return f([u.cata(f) if isinstance(u, Template) else u for u in self._tree])

    def __repr__(self) -> str:
        return f"<template>{"".join(map(str, iter(self)))}</template>"

    def __iter__(self) -> Iterator[TemplatePart]:
        for x in self._tree:
            match x:
                case Template():
                    yield from x
                case _:
                    yield x
