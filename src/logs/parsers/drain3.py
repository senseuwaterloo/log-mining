from argparse import ArgumentParser, FileType
import sys
from typing import Any, Callable, Generator, Iterable, Iterator, Optional, Sequence
from drain3 import TemplateMiner
from drain3.drain import LogCluster
from drain3.masking import MaskingInstruction
from drain3.template_miner_config import TemplateMinerConfig
from logs.event import Event

from logs.templates import Template, TemplateBase, TemplateStatic, TemplateVariable
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
    patterns["email"] = r"([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x22([^\x0d\x22\x5c\x80-\xff]|\x5c[\x00-\x7f])*\x22))*\x40([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d)(\x2e([^\x00-\x20\x22\x28\x29\x2c\x2e\x3a-\x3c\x3e\x40\x5b-\x5d\x7f-\xff]+|\x5b([^\x0d\x5b-\x5d\x80-\xff]|\x5c[\x00-\x7f])*\x5d))*"
    patterns["mac"] = r"(?:[a-zA-Z0-9]{2}[:-]){5}[a-zA-Z0-9]{2}"
    patterns["ipv4"] = r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    patterns["ipv6"] = r"((([0-9A-Fa-f]{1,4}:){1,6}:)|(([0-9A-Fa-f]{1,4}:){7}))([0-9A-Fa-f]{1,4})"

    for dtype, pattern in patterns:
        config.masking_instructions.append(MaskingInstruction(pattern, mask_with=dtype))

    patterns["*"] = ".+?"

    miner = TemplateMiner(config=config)

    def mkparts(template: str, types: Sequence[str]) -> Generator[TemplateVariable | TemplateStatic, None, None]:
        head, *tail = re.split(r"<.*?>", template)
        if len(tail) != len(types):
            raise UnmatchedParameters(f"{types} {template}")
        yield TemplateStatic(head)
        for position, (part, type) in enumerate(zip(tail, types)):
            yield TemplateVariable(patterns, position, type)
            yield TemplateStatic(part)

    def mktemplate(template: str, types: Sequence[str]):
        return Template(*mkparts(template, types))

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
        if match := miner.match(line, full_search_strategy="fallback") is not None:
            id, template = extract(match)
            return mkevent(id, template, line)

    def train(line: str):
        line = line.strip()
        id, template = itemgetter("cluster_id", "template_mined")(miner.add_log_message(line))
        return mkevent(id, template, line)

    return train, parse

    
def main():
    argparser = ArgumentParser()
    argparser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin)
    args = argparser.parse_args()
    train, _ = parser()
    try:
        for event in map(train, args.file):
            print(repr(event))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
