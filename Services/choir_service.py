"""Application services and business rules for choir administration."""

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import cast

from Data.models import (
    AttendanceChart,
    AttendanceStatus,
    AttendanceSummary,
    Category,
    DashboardSummary,
    Event,
    EventInput,
    Member,
    MemberInput,
    Role,
    SchoolYear,
    Song,
    SongInput,
    StatusTotals,
    Transaction,
    TransactionInput,
    TreasurySummary,
    Voice,
    VoiceCount,
    User,
)
from Data.repository import ChoirRepository
from Services.auth_service import AuthService


MONTHS = {1:"jan.",2:"feb.",3:"mar.",4:"apr.",5:"maj",6:"jun.",7:"jul.",8:"avg.",9:"sep.",10:"okt.",11:"nov.",12:"dec."}
STATUS_KEYS: list[AttendanceStatus] = ["present", "late_under", "late_over", "excused", "absent"]
ATTENDED_STATUSES: tuple[AttendanceStatus, ...] = ("present", "late_under", "late_over")


def date_label(value: date | datetime | None, include_year: bool = True) -> str:
    if not value:
        return "Še ni izvedena"
    suffix = f" {value.year}" if include_year else ""
    return f"{value.day}. {MONTHS[value.month]}{suffix}"


class ChoirService:
    def __init__(self, repository: ChoirRepository | None = None) -> None:
        self.repository = repository or ChoirRepository()
        self.auth = AuthService(self.repository)

    @staticmethod
    def initials(first_name: str, last_name: str) -> str:
        return f"{first_name[:1]}{last_name[:1]}".upper()

    @staticmethod
    def _member_view(member: Member) -> Member:
        return replace(
            member,
            name=f"{member.first_name} {member.last_name}",
            initials=ChoirService.initials(member.first_name, member.last_name),
            birth=date_label(member.birth_date) if member.birth_date else "—",
        )

    @staticmethod
    def _status_totals(statuses: Sequence[AttendanceStatus]) -> StatusTotals:
        counts = Counter(statuses)
        return StatusTotals(
            present=counts["present"],
            late_under=counts["late_under"],
            late_over=counts["late_over"],
            excused=counts["excused"],
            absent=counts["absent"],
        )

    def members(self) -> list[Member]:
        return [self._member_view(member) for member in self.repository.list_members()]

    def member(self, member_id: int) -> Member | None:
        member = self.repository.get_member(member_id)
        if not member:
            return None
        attendance_rows = [
            replace(
                item,
                title=item.name,
                kind=item.event_type,
                date=date_label(item.event_date),
            )
            for item in self.repository.member_attendance(member_id)
        ]
        return replace(
            self._member_view(member),
            attendance_rows=attendance_rows,
            attendance_totals=self._status_totals([item.status for item in attendance_rows]),
        )

    def create_member(self, values: MemberInput, role_names: Sequence[str]) -> tuple[int, str]:
        username = self.auth.next_username(values["first_name"], values["last_name"])
        person_id = self.repository.create_member(
            values,
            username,
            self.auth.hash_password(username),
            role_names,
        )
        return person_id, username

    def update_member(
        self,
        actor: User,
        member_id: int,
        values: MemberInput,
        role_names: Sequence[str],
    ) -> None:
        is_admin = "admin" in self.auth.permissions(actor)
        if not is_admin and actor.person_id != member_id:
            raise PermissionError("Urejaš lahko samo svoje podatke.")
        if not self.repository.get_member(member_id):
            raise LookupError("Član ne obstaja.")
        self.repository.update_member(member_id, values)
        if is_admin:
            self.repository.set_member_roles(member_id, role_names)

    def delete_member(self, actor: User, member_id: int) -> None:
        if actor.person_id == member_id:
            raise ValueError("Svojega računa ne moreš izbrisati.")
        self.repository.delete_member(member_id)

    def songs(self) -> list[Song]:
        return [
            replace(
                song,
                added=date_label(song.created_at),
                last=date_label(song.last_performed),
                rating=float(song.rating or 0),
            )
            for song in self.repository.list_songs()
        ]

    def categories(self) -> list[Category]:
        return self.repository.list_categories()

    def create_category(self, name: str, description: str) -> int:
        return self.repository.create_category(name, description)

    def update_category(self, category_id: int, name: str, description: str) -> None:
        self.repository.update_category(category_id, name, description)

    def delete_category(self, category_id: int) -> bool:
        return bool(self.repository.delete_category(category_id))

    def create_song(self, values: SongInput, categories: Sequence[str]) -> int:
        return self.repository.create_song(values, categories)

    def update_song(
        self,
        song_id: int,
        values: SongInput,
        categories: Sequence[str],
    ) -> None:
        self.repository.update_song(song_id, values, categories)

    def delete_song(self, song_id: int) -> None:
        self.repository.delete_song(song_id)

    def save_review(
        self,
        person_id: int,
        song_id: int,
        rating: int,
        comment: str,
    ) -> None:
        if rating not in range(1, 6):
            raise ValueError("Ocena mora biti med 1 in 5.")
        self.repository.upsert_review(person_id, song_id, rating, comment)

    def song(self, song_id: int, person_id: int | None = None) -> Song | None:
        song = self.repository.get_song(song_id)
        if not song:
            return None
        performances = [
            replace(
                performance,
                title=performance.name,
                kind=performance.event_type,
                date=date_label(performance.event_date),
            )
            for performance in song.performances
        ]
        my_review = next(
            (review for review in song.reviews if review.person_id == person_id),
            None,
        )
        return replace(
            song,
            added=date_label(song.created_at),
            last=date_label(song.last_performed),
            rating=float(song.rating or 0),
            performances=performances,
            my_review=my_review,
        )

    def events(self) -> list[Event]:
        now = datetime.now().astimezone()
        events = [self._event_view(event, now) for event in self.repository.list_events()]
        return sorted(
            events,
            key=lambda event: (
                event.status == "past",
                event.event_date if event.status == "upcoming" else -event.event_date.timestamp(),
            ),
        )

    def event_types(self) -> list[str]:
        return self.repository.list_event_types()

    def calendar_events(self) -> list[Event]:
        return self.repository.list_events()

    def create_event(self, values: EventInput, song_ids: Sequence[int]) -> int:
        return self.repository.create_event(values, song_ids)

    def update_event(
        self,
        event_id: int,
        values: EventInput,
        song_ids: Sequence[int],
    ) -> None:
        self.repository.update_event(event_id, values, song_ids)

    def delete_event(self, event_id: int) -> None:
        self.repository.delete_event(event_id)

    def update_performance(
        self,
        actor: User,
        event_id: int,
        song_id: int,
        rating: int,
        comment: str,
    ) -> None:
        if not self.auth.is_conductor(actor):
            raise PermissionError("Ocene izvedb lahko ureja samo zborovodja.")
        if rating not in range(1, 6):
            raise ValueError("Ocena mora biti med 1 in 5.")
        self.repository.update_performance(event_id, song_id, rating, comment)

    def event(self, event_id: int) -> Event | None:
        event = self.repository.get_event(event_id)
        return self._event_view(event, datetime.now().astimezone()) if event else None

    @staticmethod
    def _event_view(event: Event, now: datetime) -> Event:
        return replace(
            event,
            date=date_label(event.event_date),
            time=event.event_date.strftime("%H:%M"),
            kind=event.event_type,
            title=event.name,
            status="upcoming" if event.event_date >= now else "past",
        )

    def roles(self) -> list[Role]:
        return self.repository.list_roles()

    def create_role(self, name: str, description: str) -> int:
        return self.repository.create_role(name, description)

    def update_role(self, role_id: int, name: str, description: str) -> None:
        self.repository.update_role(role_id, name, description)

    def delete_role(self, role_id: int) -> bool:
        return bool(self.repository.delete_role(role_id))

    @staticmethod
    def school_year_start(value: date | datetime) -> int:
        return value.year if value.month >= 9 else value.year - 1

    @staticmethod
    def event_group(event_type: str) -> str:
        lowered = event_type.lower()
        if "vaja" in lowered:
            return "Vaje"
        if "koncert" in lowered:
            return "Koncerti"
        return "Ostalo"

    def attendance(
        self,
        selected_year: str | None = None,
        selected_type: str = "Vse",
    ) -> AttendanceSummary:
        members = self.members()
        all_events = self.events()
        records = self.repository.list_attendance()
        years = sorted(
            {self.school_year_start(event.event_date) for event in all_events},
            reverse=True,
        )
        current_start = self.school_year_start(datetime.now().astimezone())
        try:
            year_start = int(selected_year) if selected_year is not None else current_start
        except ValueError:
            year_start = current_start
        if years and year_start not in years:
            year_start = years[0]
        events = [
            event
            for event in all_events
            if self.school_year_start(event.event_date) == year_start
            and (
                selected_type in (None, "", "Vse")
                or self.event_group(event.event_type) == selected_type
            )
        ]
        lookup = {(item.person_id, item.event_id): item.status for item in records}
        matrix: list[list[AttendanceStatus]] = [
            [lookup.get((member.id, event.id), "absent") for event in events]
            for member in members
        ]
        member_totals = [self._status_totals(row) for row in matrix]
        event_totals = [
            self._status_totals([row[column] for row in matrix])
            for column in range(len(events))
        ]
        total_records = max(len(members) * len(events), 1)
        attended = sum(
            sum(total[state] for state in ATTENDED_STATUSES)
            for total in member_totals
        )
        voices = {member.voice for member in members}
        voice_rates = {
            voice: round(
                100
                * sum(
                    sum(state in ATTENDED_STATUSES for state in matrix[index])
                    for index, member in enumerate(members)
                    if member.voice == voice
                )
                / max(sum(member.voice == voice for member in members) * len(events), 1)
            )
            for voice in voices
        }
        return AttendanceSummary(
            members=members,
            events=events,
            status_keys=STATUS_KEYS,
            matrix=matrix,
            member_totals=member_totals,
            event_totals=event_totals,
            average=round(100 * attended / total_records),
            event_count=len(events),
            best_voice=max(voice_rates, key=voice_rates.get) if voice_rates else "—",
            best_voice_rate=max(voice_rates.values()) if voice_rates else 0,
            school_years=[SchoolYear(year, f"{year}/{str(year + 1)[-2:]}") for year in years],
            selected_year=year_start,
            selected_type=selected_type or "Vse",
            chart_data=AttendanceChart(
                labels=[event.date.replace(" 2026", "") for event in events],
                voices=[member.voice for member in members],
                matrix=matrix,
                statuses=STATUS_KEYS,
            ),
        )

    def save_attendance(
        self,
        event_id: int,
        person_id: int,
        status: str,
        user_id: int,
    ) -> None:
        if status not in STATUS_KEYS:
            raise ValueError("Neveljaven status.")
        self.repository.upsert_attendance(
            event_id,
            person_id,
            cast(AttendanceStatus, status),
            user_id,
        )

    def treasury(self) -> TreasurySummary:
        transactions: list[Transaction] = [
            replace(
                transaction,
                date=date_label(transaction.transaction_date),
                raw_date=transaction.transaction_date,
                person=transaction.person_name,
            )
            for transaction in self.repository.list_transactions()
        ]
        zero = Decimal("0")
        income = sum(
            (item.amount for item in transactions if item.kind == "Prihodek"),
            zero,
        )
        expenses = sum(
            (item.amount for item in transactions if item.kind == "Odhodek"),
            zero,
        )
        unsettled = sum(
            (item.amount for item in transactions if not item.settled),
            zero,
        )
        return TreasurySummary(
            transactions=transactions,
            income=income,
            expenses=expenses,
            balance=income - expenses,
            unsettled=unsettled,
        )

    def create_transaction(self, values: TransactionInput, user_id: int) -> int:
        return self.repository.create_transaction(values, user_id)

    def set_transaction_settled(self, transaction_id: int, settled: bool) -> None:
        self.repository.set_transaction_settled(transaction_id, settled)

    def update_transaction(self, transaction_id: int, values: TransactionInput) -> None:
        self.repository.update_transaction(transaction_id, values)

    def dashboard(self) -> DashboardSummary:
        members = self.members()
        songs = self.songs()
        events = self.events()
        voice_counts = Counter(member.voice for member in members)
        ranked = sorted(members, key=lambda member: member.attendance, reverse=True)
        return DashboardSummary(
            member_count=len(members),
            voices=[VoiceCount(voice, count) for voice, count in voice_counts.items()],
            top_members=ranked[:3],
            low_members=list(reversed(ranked[-3:])),
            song_count=len(songs),
            latest_songs=songs[:3],
            forgotten_songs=sorted(songs, key=lambda song: song.last or "")[:3],
            events=events,
            attendance=ranked,
            upcoming_count=sum(event.status == "upcoming" for event in events),
            average_attendance=round(
                sum(member.attendance for member in members) / max(len(members), 1)
            ),
        )
