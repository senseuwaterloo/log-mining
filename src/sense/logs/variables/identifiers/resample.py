from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence, TextIO
from logs.event import Event, Parameter
from logs.parsers.drain3 import parser

import numpy as np

from numpy.typing import NDArray
from scipy.stats import gaussian_kde
from tqdm import tqdm
from itertools import chain


class Distribution:
    _sampling_function: Callable[[int], NDArray[Any]]

    def __init__(self, population: Sequence[Parameter], seed: int | None = None):
        _rng = np.random.default_rng(seed=seed)
        _population = np.array([p.value for p in population])

        try:
            _population = _population.astype("int64")
            _dist = gaussian_kde(_population)
            self._sampling_function = lambda size: _dist.resample(size, _rng).astype(
                "int64"
            )
            return
        except TypeError:
            pass
        except ValueError:
            pass

        try:
            _population = _population.astype("float64")
            _dist = gaussian_kde(_population)
            self._sampling_function = lambda size: _dist.resample(size, _rng)
            return
        except TypeError:
            pass
        except ValueError:
            pass

        self._sampling_function = lambda size: _rng.choice(_population, size)

    def sample(self, size):
        return self._sampling_function(size)


def mkdatasets(events: Iterable[Event]):
    datasets = defaultdict(list)
    for event in events:
        for parameter in event.parameters:
            datasets[(event.id, parameter.position)] += [parameter]
    return {index: Distribution(values) for index, values in datasets.items()}


def main(trainfiles: list[TextIO], files: list[TextIO], output: TextIO):
    train, parse = parser()

    if len(trainfiles) <= 0:
        raise RuntimeError("no training files")

    lines = list(chain(*trainfiles))
    datasets = mkdatasets(tqdm(map(train, lines), total=len(lines), desc="training"))

    for line in chain(*files):
        if (event := parse(line)) is None:
            raise RuntimeError(f"{line} can not be parsed")
        for parameter in event.parameters:
            parameter.value = str(
                datasets[(parameter.event.id, parameter.position)].sample(1).item()
            )
        print(event.text.strip(), file=output)


if __name__ == "__main__":
    import argparse
    import sys

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--train", type=argparse.FileType("r"), nargs="*", default=[]
    )
    argparser.add_argument(
        "files", type=argparse.FileType("r"), nargs="*", default=[sys.stdin]
    )
    argparser.add_argument(
        "output", type=argparse.FileType("w"), nargs="?", default=sys.stdout
    )
    ns = argparser.parse_args()
    main(ns.train, ns.files, ns.output)
