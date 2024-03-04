from argparse import ArgumentParser, FileType
import sys
from typing import Iterator, Optional, Sequence
from drain3 import TemplateMiner
from drain3.drain import LogCluster
from drain3.masking import MaskingInstruction
from drain3.template_miner_config import TemplateMinerConfig
from logs.event import Event

from logs.templates import Template, TemplatePart, Variable
from logs.patterns import PatternStore

import re

from operator import itemgetter


class UnmatchedParameters(RuntimeError):
    pass


def parser():
    config = TemplateMinerConfig()
    config.mask_prefix = "<"
    config.mask_suffix = ">"

    patterns = PatternStore()

    for dtype, pattern in patterns:
        config.masking_instructions.append(MaskingInstruction(pattern, mask_with=dtype))

    patterns["*"] = ".+?"

    miner = TemplateMiner(config=config)

    def mkparts(template: str, types: Sequence[str]) -> Iterator[TemplatePart]:
        head, *tail = re.split(r"<.*?>", template)
        if len(tail) != len(types):
            raise UnmatchedParameters(f"{types} {template}")
        yield head
        for part, type in zip(tail, types):
            yield Variable(type)
            yield part

    def mktemplate(template: str, types: Sequence[str]):
        return Template([*mkparts(template, types)])

    def mkevent(id: int, template: str, line: str):
        params = miner.extract_parameters(template, line)
        if not params:
            return Event(id, mktemplate(template, []), [])
        types, values = zip(*((p.mask_name, p.value) for p in params))
        return Event(id, mktemplate(template, types), list(values))

    def extract(logcluster: LogCluster):
        return logcluster.cluster_id, logcluster.get_template()

    def parse(line: str) -> Optional[Event]:
        line = line.strip()
        if (match := miner.match(line, full_search_strategy="fallback")) is not None:
            id, template = extract(match)
            return mkevent(id, template, line)

    def train(line: str):
        line = line.strip()
        id, template = itemgetter("cluster_id", "template_mined")(
            miner.add_log_message(line)
        )
        return mkevent(id, template, line)

    return train, parse


def main():
    argparser = ArgumentParser()
    argparser.add_argument("file", nargs="?", type=FileType("r"), default=sys.stdin)
    args = argparser.parse_args()
    train, _ = parser()
    try:
        for event in map(train, args.file):
            print(repr(event))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
