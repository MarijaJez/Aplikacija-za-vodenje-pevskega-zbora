"""Authentication business rules for account provisioning."""

import re
import unicodedata

import bcrypt

from Data.models import Permission, User
from Data.repository import ChoirRepository


class AuthService:
    def __init__(self, repository: ChoirRepository | None = None) -> None:
        self.repository = repository or ChoirRepository()

    @staticmethod
    def _slug(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", "", ascii_value)

    @staticmethod
    def initial_password(username: str) -> str:
        return username

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.repository.get_user_by_username(username)
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            return None
        self.repository.record_login(user.id)
        return user

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get_user_by_id(user_id)

    @staticmethod
    def permissions(user: User | None) -> set[Permission]:
        if not user:
            return set()
        roles = set(user.roles)
        if roles & {"Predsednik", "Zborovodja"}:
            return {"admin", "program", "attendance", "treasury", "self"}
        permissions: set[Permission] = {"self"}
        if "Notar" in roles:
            permissions.add("program")
        if "Blagajnik" in roles:
            permissions.add("treasury")
        if "Beleženje prisotnosti" in roles:
            permissions.add("attendance")
        return permissions

    @staticmethod
    def is_conductor(user: User) -> bool:
        return "Zborovodja" in user.roles

    def next_username(self, first_name: str, last_name: str) -> str:
        base = f"{self._slug(first_name)}.{self._slug(last_name)}"
        username = base
        suffix = 1
        while self.repository.username_exists(username):
            username = f"{base}{suffix}"
            suffix += 1
        return username

    def change_password(self, user_id: int, password: str) -> None:
        if len(password) < 8:
            raise ValueError("Geslo mora vsebovati vsaj 8 znakov.")
        user = self.repository.get_user_by_id(user_id)
        if not user or password == user.username:
            raise ValueError("Geslo ne sme biti enako uporabniškemu imenu.")
        self.repository.change_password(user_id, self.hash_password(password), must_change=False)

    def change_initial_password(
        self,
        user_id: int,
        password: str,
        confirmation: str,
    ) -> None:
        if password != confirmation:
            raise ValueError("Gesli se ne ujemata.")
        self.change_password(user_id, password)

    def change_own_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirmation: str,
    ) -> None:
        if new_password != confirmation:
            raise ValueError("Novi gesli se ne ujemata.")
        user = self.repository.get_user_by_id(user_id)
        if not user or not bcrypt.checkpw(current_password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise ValueError("Trenutno geslo ni pravilno.")
        self.change_password(user_id, new_password)

    def reset_password(self, person_id: int) -> str:
        member = self.repository.get_member(person_id)
        if not member:
            raise ValueError("Član ne obstaja.")
        user = self.repository.get_user_by_username(member.username)
        if not user:
            raise ValueError("Uporabniški račun ne obstaja.")
        self.repository.change_password(user.id, self.hash_password(user.username), must_change=True)
        return user.username
