from argparse import ArgumentParser, FileType
from collections import defaultdict
import sys
from typing import Any, Callable, Dict, Generator, Iterable, Sequence, Set, Tuple
from drain3 import TemplateMiner
from drain3.template_miner import ExtractedParameter
from drain3.template_miner_config import TemplateMinerConfig
from random import choice
from logs.event import Event

from logs.templates import Template, TemplateBase, TemplateStatic, TemplateVariable
from logs.patterns import PatternStore
from string import ascii_letters, digits
from operator import itemgetter


class UnmatchedParameters(RuntimeError):
    pass
    

def parser(sample: Iterable[str] | None=None, mask:bool = False, shuffle: bool = False, fuzz: bool = False, varset_size: int = 10) -> Callable[[str], Any]:
    config = TemplateMinerConfig()
    miner = TemplateMiner(config=config)
    if sample is not None:
        for line in sample:
            miner.add_log_message(line)

    varset: Dict[Tuple[int, int], Set[ExtractedParameter]] = defaultdict(set)

    templates: dict[int, Template] = {}

    patterns = PatternStore()
    patterns["*"] = ".*"
    patterns["0"] = ".*"

    def fuzzy(text: Iterable[str]) -> Generator[str, None, None]:
        for part in text:
            if part.isdecimal():
                yield choice(digits)
            elif part.isalpha():
                yield choice(ascii_letters)
            else:
                yield part

    def mkparts(template: str, types: Sequence[str]) -> Generator[TemplateBase, None, None]:
        head, *tail = template.split("<*>")
        if len(tail) != len(types):
            raise UnmatchedParameters(f"{template} {types}")
        yield TemplateStatic(head)
        for part, type in zip(tail, types):
            yield TemplateVariable(patterns, type, type)
            yield TemplateStatic(part)

    def mktemplate(id, template: str, types: Sequence[str]):
        templates[id] = Template(*mkparts(template, types))
        return templates[id]

    def mkevent(id: int, template: str, line: str):
        params = miner.extract_parameters(template, line.strip(), exact_matching=False)
        if not params:
            return Event(id, mktemplate(id, template, []), [])
        types, values = zip(*((p.mask_name, p.value) for p in params))
        return Event(id, mktemplate(id, template, types), list(values))
        
    extract = itemgetter("cluster_id", "template_mined")
    def parse(line: str) -> Event:
        id, template = extract(miner.add_log_message(line))
        return mkevent(id, template, line)

    return parse
        
    


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument("--mask", action="store_true")
    argparser.add_argument("--shuffle", action="store_true")
    argparser.add_argument("--fuzz", action="store_true")
    argparser.add_argument("--varset_size", type=int, default=10)
    argparser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin)
    args = argparser.parse_args()
    parse = parser([], mask=args.mask, shuffle=args.shuffle, fuzz=args.fuzz, varset_size=args.varset_size)
    try:
        for line in args.file:
            print(repr(parse(line)))
    except KeyboardInterrupt:
        pass
