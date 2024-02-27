from ..event import Event
from ..templates import Template, Variable


import csv
import sys


LABEL_MAP = {
    "": "unsensitive",
    "i": "ip",
    "p": "port",
    "l": "uri",
    "g": "guid",
    "u": "user",
    "w": "pass",
    "k": "key",
    "s": "sess",
    "f": "file",
    "d": "date",
    "h": "phone",
    "n": "name",
    "v": "value",
    "o": "other"
}

class Dataset:
    save_path: str
    events: list[Event]
    labels: list[list[str]]

    def __init__(self, logfile_path, save_path):
        self.save_path = save_path
        self.events = []
        self.labels = []
        with open(logfile_path) as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                self.add(row["EventTemplate"], row["Content"])
        try:
            with open(save_path) as f:
                for row in f:
                    row = row.strip()
                    if row == "":
                        self.labels.append([])
                    else:
                        self.labels.append(row.split(","))
        except FileNotFoundError:
            pass
                


    def add(self, template_string: str, content: str):
        template = Template.from_xml(template_string)
        if m := template.regex.match(content):
            event = Event(len(self.events), template, [*m.groups()])
            self.events.append(event)
            return
            
        raise RuntimeError("failed to match template with content", template_string, template.regex, content)

    def task(self, i, j):
        event = self.events[i]
        parts = []
        k = 0
        for part in event.template:
            match part:
                case str():
                    parts.append(part)
                case Variable():
                    if k == j:
                        parts.append(f"\033[4;7m{event.values[k]}\033[0m")
                    else:
                        parts.append(event.values[k])
                    k += 1
        string = f"{i} " + "".join(parts)
        while True:
            try:
                print(string, end=" ")
                return LABEL_MAP[input()]
            except KeyError:
                continue

    def label_all(self):
        print(LABEL_MAP)
        try:
            for i, event in enumerate(self.events):
                while i >= len(self.labels):
                    self.labels.append([])
                for j, _ in enumerate(event.values):
                    while j >= len(self.labels[i]):
                        self.labels[i].append(self.task(i, len(self.labels[i])))
        finally:
            with open(self.save_path, "w") as f:
                f.writelines(",".join(l) + "\n" for l in self.labels)



def main(*argv):
    ds = Dataset(*argv[1:])
    ds.label_all()

if __name__ == "__main__":
    try:
        main(*sys.argv)
    except KeyboardInterrupt:
        pass
