"""Opt-in Web Push subscriptions and event announcements."""

import base64
import json
import logging
import os
import re
import secrets
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from bottle import HTTPError, request, response
from pywebpush import WebPushException, webpush


LOG = logging.getLogger(__name__)
_DELIVERY_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="choir-push")
_ALLOWED_HOSTS = {
    "fcm.googleapis.com",
    "updates.push.services.mozilla.com",
    "web.push.apple.com",
}


def _valid_endpoint(endpoint):
    if not isinstance(endpoint, str) or len(endpoint) > 2048:
        return False
    try:
        parsed = urlparse(endpoint)
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
            and not parsed.fragment
            and (host in _ALLOWED_HOSTS or host.endswith(".notify.windows.com"))
        )
    except ValueError:
        return False


def _valid_key(value, expected_bytes):
    if not isinstance(value, str) or len(value) > 128 or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return False
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        return len(decoded) == expected_bytes
    except (ValueError, TypeError):
        return False


class PushNotificationService:
    def __init__(self, repository):
        self.db = repository.db
        self.public_key = os.getenv("VAPID_PUBLIC_KEY", "").strip()
        self.private_key_file = os.getenv("VAPID_PRIVATE_KEY_FILE", "").strip()
        self.contact = os.getenv("VAPID_CONTACT_EMAIL", "mladinskipevskizborhomec@gmail.com").strip()

    @property
    def configured(self):
        return bool(self.public_key and self.private_key_file and self.contact and os.path.isfile(self.private_key_file))

    def register_routes(self, app, current_user, require_login, app_base_url):
        allowed_origin = f"{urlparse(app_base_url).scheme}://{urlparse(app_base_url).netloc}"

        def check_post():
            if request.get_header("Origin") != allowed_origin:
                raise HTTPError(403, "Neveljaven izvor zahteve.")
            length = request.content_length
            if request.content_type != "application/json" or length is None or length < 0 or length > 8192:
                raise HTTPError(400, "Pričakovani so podatki JSON.")

        @app.get("/api/push/config")
        @require_login
        def push_config():
            response.set_header("Cache-Control", "no-store")
            response.content_type = "application/json"
            return {"enabled": self.configured, "publicKey": self.public_key if self.configured else ""}

        @app.get("/api/push/status")
        @require_login
        def push_status():
            response.set_header("Cache-Control", "no-store")
            response.content_type = "application/json"
            endpoint = request.query.get("endpoint", "")
            if not _valid_endpoint(endpoint):
                raise HTTPError(400, "Neveljaven naslov naročnine.")
            with self.db.cursor() as cur:
                cur.execute("SELECT user_id FROM push_subscriptions WHERE endpoint=%s", (endpoint,))
                row = cur.fetchone()
            return {"subscribed": bool(row and row["user_id"] == current_user()["id"])}

        @app.post("/api/push/subscriptions")
        @require_login
        def subscribe():
            check_post()
            if not self.configured:
                raise HTTPError(503, "Obvestila še niso nastavljena.")
            data = request.json or {}
            if not isinstance(data, dict):
                raise HTTPError(400, "Neveljavna naročnina na obvestila.")
            endpoint = data.get("endpoint")
            keys = data.get("keys") or {}
            if not isinstance(keys, dict) or not _valid_endpoint(endpoint) or not _valid_key(keys.get("p256dh"), 65) or not _valid_key(keys.get("auth"), 16):
                raise HTTPError(400, "Neveljavna naročnina na obvestila.")
            with self.db.cursor() as cur:
                cur.execute(
                    """INSERT INTO push_subscriptions(endpoint,user_id,p256dh,auth)
                       VALUES(%s,%s,%s,%s)
                       ON CONFLICT(endpoint) DO UPDATE SET user_id=EXCLUDED.user_id,
                           p256dh=EXCLUDED.p256dh,auth=EXCLUDED.auth,updated_at=NOW()""",
                    (endpoint, current_user()["id"], keys["p256dh"], keys["auth"]),
                )
            response.status = 201
            response.content_type = "application/json"
            return {"subscribed": True}

        @app.post("/api/push/unsubscribe")
        @require_login
        def unsubscribe():
            check_post()
            data = request.json or {}
            if not isinstance(data, dict):
                raise HTTPError(400, "Neveljavna naročnina na obvestila.")
            endpoint = data.get("endpoint")
            if not _valid_endpoint(endpoint):
                raise HTTPError(400, "Neveljaven naslov naročnine.")
            with self.db.cursor() as cur:
                cur.execute("DELETE FROM push_subscriptions WHERE endpoint=%s AND user_id=%s", (endpoint, current_user()["id"]))
            response.content_type = "application/json"
            return {"subscribed": False}

        @app.post("/api/push/test")
        @require_login
        def test_push():
            check_post()
            if not self.configured:
                raise HTTPError(503, "Obvestila še niso nastavljena.")
            self.notify("Preizkusno obvestilo", "Obvestila iz aplikacije delujejo.", "/dogodki", recipient_user_id=current_user()["id"])
            response.content_type = "application/json"
            return {"queued": True}

    def notify_event(self, action, event):
        """Queue a best-effort message for every opted-in browser."""
        if not self.configured or action not in {"created", "updated", "deleted"}:
            return
        title = {"created": "Nov zborovski dogodek", "updated": "Dogodek je spremenjen", "deleted": "Dogodek je odpovedan"}[action]
        when = event.get("event_date")
        date_label = when.strftime("%d. %m. %Y ob %H:%M") if hasattr(when, "strftime") else ""
        body = f"{event['name']} · {date_label}" if date_label else str(event["name"])
        self.notify(title, body, f"/dogodki/{event['id']}" if action != "deleted" else "/dogodki", tag=f"event-{event['id']}")

    def notify(self, title, body, url, exclude_user_id=None, tag=None, recipient_user_id=None):
        """Queue a visible notification; reusable for chat and other member updates."""
        if not self.configured:
            return
        if not isinstance(url, str) or not url.startswith("/") or url.startswith("//"):
            raise ValueError("Push target must be a local path")
        payload = json.dumps({"title": str(title)[:100], "body": str(body)[:300], "url": url, "tag": tag or secrets.token_urlsafe(8)}, ensure_ascii=False)
        try:
            _DELIVERY_POOL.submit(self._deliver, payload, exclude_user_id, recipient_user_id)
        except RuntimeError:
            LOG.exception("Push worker is unavailable")

    def _deliver(self, payload, exclude_user_id=None, recipient_user_id=None):
        try:
            with self.db.cursor() as cur:
                cur.execute("""SELECT endpoint,p256dh,auth FROM push_subscriptions
                    WHERE (%s::BIGINT IS NULL OR user_id<>%s)
                      AND (%s::BIGINT IS NULL OR user_id=%s)""", (exclude_user_id, exclude_user_id, recipient_user_id, recipient_user_id))
                subscriptions = cur.fetchall()
        except Exception:
            LOG.exception("Could not load push subscriptions")
            return
        for subscription in subscriptions:
            endpoint = subscription["endpoint"]
            try:
                headers = {"X-WNS-Type": "wns/toast"} if urlparse(endpoint).hostname.endswith(".notify.windows.com") else None
                webpush(
                    subscription_info={"endpoint": endpoint, "keys": {"p256dh": subscription["p256dh"], "auth": subscription["auth"]}},
                    data=payload,
                    vapid_private_key=self.private_key_file,
                    vapid_claims={"sub": f"mailto:{self.contact}"},
                    ttl=3600,
                    timeout=5,
                    headers=headers,
                )
            except WebPushException as exc:
                status_code = getattr(exc.response, "status_code", None)
                if status_code in (404, 410):
                    with self.db.cursor() as cur:
                        cur.execute("DELETE FROM push_subscriptions WHERE endpoint=%s", (endpoint,))
                else:
                    LOG.warning("Push delivery failed with HTTP %s", status_code)
            except Exception:
                LOG.exception("Push delivery failed")
