"""Small server-side Google OAuth 2.0/OpenID Connect client."""

import base64
import hashlib
import os
import secrets
from urllib.parse import urlencode

import requests
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token


AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class GoogleOAuthError(RuntimeError):
    pass


class GoogleOAuthClient:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

    @property
    def configured(self):
        return bool(self.client_id and self.client_secret)

    @staticmethod
    def new_flow_values():
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        return {
            "state": secrets.token_urlsafe(32),
            "nonce": secrets.token_urlsafe(32),
            "verifier": verifier,
            "challenge": challenge,
        }

    def authorization_url(self, redirect_uri, scopes, flow, *, offline=False):
        if not self.configured:
            raise GoogleOAuthError("Google prijava še ni nastavljena.")
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": flow["state"],
            "nonce": flow["nonce"],
            "code_challenge": flow["challenge"],
            "code_challenge_method": "S256",
            "include_granted_scopes": "true",
        }
        if offline:
            params.update({"access_type": "offline", "prompt": "consent", "select_account": "true"})
        return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

    def exchange_code(self, code, redirect_uri, verifier):
        try:
            result = requests.post(TOKEN_ENDPOINT, data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            }, timeout=15)
            result.raise_for_status()
            payload = result.json()
        except (requests.RequestException, ValueError) as error:
            raise GoogleOAuthError("Google ni potrdil prijave. Poskusi znova.") from error
        if not payload.get("id_token") or not payload.get("access_token"):
            raise GoogleOAuthError("Google je vrnil nepopoln odgovor.")
        return payload

    def verify_identity(self, raw_id_token, expected_nonce):
        try:
            claims = id_token.verify_oauth2_token(raw_id_token, GoogleRequest(), self.client_id)
        except Exception as error:
            raise GoogleOAuthError("Google identitete ni bilo mogoče varno preveriti.") from error
        if claims.get("nonce") != expected_nonce:
            raise GoogleOAuthError("Prijavna zahteva je potekla ali ni veljavna.")
        if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
            raise GoogleOAuthError("Izdajatelj Google identitete ni veljaven.")
        return claims
