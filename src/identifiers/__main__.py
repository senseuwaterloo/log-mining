from collections import defaultdict
from functools import partial
from typing import Any, Callable, Generator, Iterable
from logs.event import Event, Parameter
from logs.parsers.drain3 import parser

import numpy as np

def coerce(parameters):
    dtypes = np.unique([p.variable.type for p in parameters])
    if len(dtypes) == 1:
        dtype = dtypes[0]
    else:
        dtype = "str"



def mkdatasets(events: Iterable[Event]):
    datasets = defaultdict(list)
    for event in events:
        for parameter in event.parameters:
            datasets[(event.id, parameter.index)] += [parameter]
    return {index: coerce(values) for index, values in datasets.items()}


def mklines(files) -> Generator[str, None, None]:
    for file in files:
        yield from file


def mask(parameter, sample):
    parameter.value = "<*/>"

def kde_sample(parameter, sample):
    pass


def main(files, output, shuffle: bool):
    lines = list(mklines(files))
    parse = parser(lines)

    events = list(map(parse, lines))

    datasets = mkdatasets(events)

    process: Callable[[Parameter, Any], None] = mask
    if shuffle:
        process = kde_sample

    for event in map(parse, lines):
        for parameter in event.parameters:
            process(parameter, datasets[(event.id, parameter.index)])



if __name__ == "__main__":
    import argparse
    import sys
    argparser = argparse.ArgumentParser()
    argparser.add_argument("files", type=argparse.FileType("rb"), nargs="*", default=[sys.stdin])
    argparser.add_argument("output", type=argparse.FileType("wb"), nargs="?", default=sys.stdout)
    argparser.add_argument("--shuffle", action="store_true")
    ns = argparser.parse_args()
    main(ns.files, ns.output, ns.shuffle)
