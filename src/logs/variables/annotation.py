from ..event import Event
from ..templates import Template
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Dataset:
    events: dict[int, list[Event]]

    @classmethod
    def fromevents(cls, events: list[Event]):
        stores = defaultdict(list)
        for event in events:
            stores[event.id].append(event)
            
        return Dataset(stores)


