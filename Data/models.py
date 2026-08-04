"""Typed domain entities, service DTOs, and repository input contracts."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field, fields
from datetime import date as Date, datetime
from decimal import Decimal
from typing import Any, Literal, NotRequired, TypedDict


Voice = Literal["Sopran", "Alt", "Tenor", "Bas"]
AttendanceStatus = Literal["present", "late_under", "late_over", "excused", "absent"]
TransactionKind = Literal["Prihodek", "Odhodek"]
Permission = Literal["admin", "program", "attendance", "treasury", "self"]


class TemplateMapping(Mapping[str, Any]):
    """Make frozen dataclasses readable both as objects and template mappings."""

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as error:
            raise KeyError(key) from error

    def __iter__(self) -> Iterator[str]:
        return (item.name for item in fields(self))

    def __len__(self) -> int:
        return len(fields(self))


@dataclass(frozen=True)
class User(TemplateMapping):
    id: int
    person_id: int
    username: str
    password_hash: str
    must_change_password: bool
    first_name: str
    last_name: str
    email: str
    roles: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Member(TemplateMapping):
    id: int
    first_name: str
    last_name: str
    birth_date: Date | None
    email: str
    phone: str
    voice: Voice
    username: str
    roles: list[str] = field(default_factory=list)
    attendance: int = 0
    must_change_password: bool = False
    name: str = ""
    initials: str = ""
    birth: str = ""
    attendance_rows: list[MemberAttendance] = field(default_factory=list)
    attendance_totals: StatusTotals | None = None


@dataclass(frozen=True)
class Role(TemplateMapping):
    id: int
    name: str
    description: str
    count: int = 0


@dataclass(frozen=True)
class Category(TemplateMapping):
    id: int
    name: str
    description: str
    count: int = 0


@dataclass(frozen=True)
class SongReview(TemplateMapping):
    rating: int
    comment: str
    updated_at: datetime
    member: str
    initials: str
    person_id: int


@dataclass(frozen=True)
class SongPerformance(TemplateMapping):
    id: int
    name: str
    event_type: str
    event_date: datetime
    place: str
    rating: int | None
    comment: str
    title: str = ""
    kind: str = ""
    date: str = ""


@dataclass(frozen=True)
class Song(TemplateMapping):
    id: int
    title: str
    author: str
    notes_path: str | None
    audio_path: str | None
    created_at: datetime
    categories: list[str] = field(default_factory=list)
    rating: float = 0.0
    ratings: int = 0
    last_performed: datetime | None = None
    reviews: list[SongReview] = field(default_factory=list)
    performances: list[SongPerformance] = field(default_factory=list)
    added: str = ""
    last: str = ""
    my_review: SongReview | None = None


@dataclass(frozen=True)
class EventProgramSong(TemplateMapping):
    id: int
    title: str
    author: str
    audio_path: str | None
    rating: int | None
    comment: str


@dataclass(frozen=True)
class Event(TemplateMapping):
    id: int
    event_date: datetime
    event_type: str
    name: str
    place: str
    created_at: datetime | None = None
    songs: int = 0
    program: list[EventProgramSong] = field(default_factory=list)
    date: str = ""
    time: str = ""
    kind: str = ""
    title: str = ""
    status: Literal["upcoming", "past"] = "upcoming"


@dataclass(frozen=True)
class AttendanceRecord(TemplateMapping):
    event_id: int
    person_id: int
    status: AttendanceStatus


@dataclass(frozen=True)
class MemberAttendance(TemplateMapping):
    id: int
    name: str
    event_type: str
    event_date: datetime
    status: AttendanceStatus
    title: str = ""
    kind: str = ""
    date: str = ""


@dataclass(frozen=True)
class Transaction(TemplateMapping):
    id: int
    transaction_date: Date
    description: str
    person_name: str
    kind: TransactionKind
    amount: Decimal
    settled: bool
    date: str = ""
    raw_date: Date | None = None
    person: str = ""


@dataclass(frozen=True)
class StatusTotals(TemplateMapping):
    present: int = 0
    late_under: int = 0
    late_over: int = 0
    excused: int = 0
    absent: int = 0


@dataclass(frozen=True)
class SchoolYear(TemplateMapping):
    start: int
    label: str


@dataclass(frozen=True)
class AttendanceChart(TemplateMapping):
    labels: list[str]
    voices: list[Voice]
    matrix: list[list[AttendanceStatus]]
    statuses: list[AttendanceStatus]


@dataclass(frozen=True)
class AttendanceSummary(TemplateMapping):
    members: list[Member]
    events: list[Event]
    status_keys: list[AttendanceStatus]
    matrix: list[list[AttendanceStatus]]
    member_totals: list[StatusTotals]
    event_totals: list[StatusTotals]
    average: int
    event_count: int
    best_voice: str
    best_voice_rate: int
    school_years: list[SchoolYear]
    selected_year: int
    selected_type: str
    chart_data: AttendanceChart


@dataclass(frozen=True)
class TreasurySummary(TemplateMapping):
    transactions: list[Transaction]
    income: Decimal
    expenses: Decimal
    balance: Decimal
    unsettled: Decimal


@dataclass(frozen=True)
class VoiceCount(TemplateMapping):
    voice: Voice
    count: int


@dataclass(frozen=True)
class DashboardSummary(TemplateMapping):
    member_count: int
    voices: list[VoiceCount]
    top_members: list[Member]
    low_members: list[Member]
    song_count: int
    latest_songs: list[Song]
    forgotten_songs: list[Song]
    events: list[Event]
    attendance: list[Member]
    upcoming_count: int
    average_attendance: int


class MemberInput(TypedDict):
    first_name: str
    last_name: str
    birth_date: NotRequired[str]
    email: str
    phone: NotRequired[str]
    voice: Voice


class SongInput(TypedDict):
    title: str
    author: str
    notes_path: NotRequired[str | None]
    audio_path: NotRequired[str | None]


class EventInput(TypedDict):
    event_date: str
    event_type: str
    name: str
    place: str


class TransactionInput(TypedDict):
    date: str
    description: str
    person_name: str
    kind: TransactionKind
    amount: str | Decimal
    settled: NotRequired[bool]
