"""Authentication business rules for account provisioning."""

import re
import secrets
import unicodedata

import bcrypt

from Data.repository import ChoirRepository


class AuthService:
    def __init__(self, repository: ChoirRepository | None = None):
        self.repository = repository or ChoirRepository()

    @staticmethod
    def _slug(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", "", ascii_value)

    def create_username(self, first_name: str, last_name: str, existing: set[str]) -> str:
        base = f"{self._slug(first_name)}.{self._slug(last_name)}"
        if base not in existing:
            return base
        suffix = 1
        while f"{base}{suffix}" in existing:
            suffix += 1
        return f"{base}{suffix}"

    @staticmethod
    def generated_password() -> str:
        """Return an unguessable placeholder for Google-first new accounts.

        It is intentionally never returned by the member creation flow or shown
        in the interface. Existing password hashes are left unchanged.
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def authenticate(self, username: str, password: str):
        user = self.repository.get_user_by_username(username)
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return None
        self.repository.record_login(user["id"])
        return user

    def authenticate_google(self, claims):
        email = (claims.get("email") or "").strip().lower()
        if claims.get("email_verified") is not True or not email:
            return None, "unverified_email"
        issuer = claims.get("iss") or ""
        subject = claims.get("sub") or ""
        if not issuer or not subject:
            return None, "invalid_identity"
        return self.repository.find_or_link_google_user(issuer, subject, email)

    def next_username(self, first_name: str, last_name: str) -> str:
        base = f"{self._slug(first_name)}.{self._slug(last_name)}"
        username = base
        suffix = 1
        while self.repository.username_exists(username):
            username = f"{base}{suffix}"
            suffix += 1
        return username

    def change_password(self, user_id: int, password: str):
        if len(password) < 8:
            raise ValueError("Geslo mora vsebovati vsaj 8 znakov.")
        user = self.repository.get_user_by_id(user_id)
        if not user or password == user["username"]:
            raise ValueError("Geslo ne sme biti enako uporabniškemu imenu.")
        self.repository.change_password(user_id, self.hash_password(password), must_change=False)

    def change_own_password(self, user_id: int, current_password: str, new_password: str):
        user = self.repository.get_user_by_id(user_id)
        if not user or not bcrypt.checkpw(current_password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            raise ValueError("Trenutno geslo ni pravilno.")
        self.change_password(user_id, new_password)
