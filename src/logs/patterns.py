from typing import Iterable, Iterator


class UndefinedPatternType(RuntimeError):
    pass


class PatternStore:
    patterns: dict[str, str]

    def __init__(self):
        self.patterns = dict()

    def __getitem__(self, type: str) -> str:
        try:
            return self.patterns[type]
        except KeyError as e:
            raise UndefinedPatternType(type) from e

    def __setitem__(self, type: str, pattern: str):
        try:
            self.patterns[type] = pattern
        except KeyError as e:
            raise UndefinedPatternType(type) from e

    def __contains__(self, type: str) -> bool:
        return type in self.patterns

    def __iter__(self) -> Iterator[tuple[str, str]]:
        return iter(self.patterns.items())
