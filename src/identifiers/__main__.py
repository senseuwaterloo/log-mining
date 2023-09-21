import argparse
import sys

from .identifiers import matcher


def main():
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
