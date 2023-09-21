from typing import Callable, Optional, Sequence, Tuple

import hyperscan as hs


def matcher(patterns: Sequence[bytes]) -> Callable[[bytes], Sequence[Tuple[int, int, bytes]]]:
    db = hs.Database()
    db.compile(expressions=patterns, flags=hs.HS_FLAG_SOM_LEFTMOST)

    class Result:
        matches: list[Tuple[int, int, bytes]]
        def __init__(self):
            self.matches = []
        def __call__(self, id, start, end, flags, context):
            self.matches += [(id, start, context[start:end])]
        def make(self) -> Sequence[Tuple[int, int, bytes]]:
            return self.matches

    def match(line: bytes) -> Sequence[Tuple[int, int, bytes]]:
        onmatch = Result()
        db.scan(line, context=line, match_event_handler=onmatch)
        return onmatch.make()

    return match
