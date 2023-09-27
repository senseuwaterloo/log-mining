from typing import Callable, Sequence, Tuple

import hyperscan as hs


def matcher(patterns: Sequence[bytes]) -> Callable[[bytes], Sequence[Tuple[int, int, bytes]]]:
    db = hs.Database()
    db.compile(expressions=patterns, flags=hs.HS_FLAG_SOM_LEFTMOST)

    class Result:
        matches: list[Tuple[int, int, bytes]]
        def __init__(self):
            self.matches = []
        def __call__(self, id, start, end, _, context):
            self.matches += [(id, start, context[start:end])]
        def make(self) -> Sequence[Tuple[int, int, bytes]]:
            return self.matches

    def match(line: bytes) -> Sequence[Tuple[int, int, bytes]]:
        onmatch = Result()
        db.scan(line, context=line, match_event_handler=onmatch)
        return onmatch.make()

    return match


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=argparse.FileType("rb"), nargs="*", default=[sys.stdin])
    parser.add_argument("output", type=argparse.FileType("wb"), nargs="?", default=sys.stdout)
    ns = parser.parse_args()

    match = matcher([b"hello", b"world"])

    try:
        for file in ns.files:
            for line in file:
                result = match(line.encode())
                print(result, file=ns.output)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
