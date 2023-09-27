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


class UnmatchedParameters(RuntimeError):
    pass
    

def parser(sample: Iterable[str] | None=None, mask:bool = False, shuffle: bool = False, fuzz: bool = False, varset_size: int = 10) -> Callable[[str], Any]:
    config = TemplateMinerConfig()
    miner = TemplateMiner(config=config)
    if sample is not None:
        for line in sample:
            miner.add_log_message(line)

    varset: Dict[Tuple[int, int], Set[ExtractedParameter]] = defaultdict(set)

    patterns = PatternStore()
    patterns['any'] = '.*'

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
            raise UnmatchedParameters
        yield TemplateStatic(head)
        for part, part_type in zip(tail, types):
            if mask:
                yield TemplateVariable(patterns, part_type, "any")
            else:
                yield TemplateVariable(patterns, part_type, part_type)
            yield TemplateStatic(part)

    def mktemplate(result, types: Sequence[str]):
        return Template(*mkparts(result["template_mined"], types))


    def mkevent(result):
        params = miner.extract_parameters(result["template_mined"], line.strip(), exact_matching=False)
        types, values = zip(*((p.mask_name, p.value) for p in params or []))
        template = mktemplate(result['template_mined'], types)
        return Event(result['cluster_id'], template, values)
        

    def parse(line: str) -> Event:
        result = miner.add_log_message(line)
        return mkevent(result)

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
    for line in args.file:
        print(repr(parse(line)))
