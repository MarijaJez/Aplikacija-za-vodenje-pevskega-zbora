"""Domain entities shared by repositories and services.

The mapping helper keeps Bottle templates compact while the application code
works with typed dataclasses, as recommended by the reference architecture.
"""

from dataclasses import dataclass, field


class TemplateMapping:
    def __getitem__(self, key):
        return getattr(self, key)


@dataclass(frozen=True)
class Member(TemplateMapping):
    id: int
    name: str
    initials: str
    voice: str
    email: str
    phone: str
    birth: str
    roles: list[str] = field(default_factory=list)
    attendance: int = 0


@dataclass(frozen=True)
class Song(TemplateMapping):
    id: int
    title: str
    author: str
    categories: list[str] = field(default_factory=list)
    rating: float = 0
    ratings: int = 0
    added: str = ""
    last: str = ""


@dataclass(frozen=True)
class Event(TemplateMapping):
    id: int
    date: str
    time: str
    kind: str
    title: str
    place: str
    status: str
    songs: int = 0


@dataclass(frozen=True)
class Role(TemplateMapping):
    name: str
    description: str
    count: int = 0


@dataclass(frozen=True)
class Transaction(TemplateMapping):
    id: int
    date: str
    description: str
    person: str
    kind: str
    amount: float
    settled: bool
