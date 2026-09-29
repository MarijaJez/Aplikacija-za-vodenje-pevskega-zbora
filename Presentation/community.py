"""Private event gallery and single choir chat route registration.

The main app passes its existing authentication/render helpers to avoid a
second session implementation. Call register_community_routes once at startup.
"""

import hashlib
import hmac
import json
import uuid
from pathlib import Path
from urllib.parse import quote_plus

from bottle import HTTPError, abort, redirect, request, response, static_file

from Data.community_repository import CommunityRepository
from Services.community_service import CommunityValidationError, clean_text, normalize_photo


def register_community_routes(app, database, render, current_user, require_login,
                              require_permission, uploads_root: Path, cookie_secret: str,
                              on_message=None):
    store = CommunityRepository(database)
    photo_dir = uploads_root / "gallery"

    def token_for(user):
        return hmac.new(cookie_secret.encode(), f"community:{user['id']}".encode(), hashlib.sha256).hexdigest()

    def check_token():
        user = current_user()
        given = request.forms.get("csrf") or request.get_header("X-CSRF-Token") or ""
        if not user or not hmac.compare_digest(given, token_for(user)):
            abort(403, "Neveljavna zaščita obrazca. Osveži stran in poskusi znova.")

    def validate_text(value, limit, label, required=False):
        try:
            return clean_text(value, limit, label, required)
        except CommunityValidationError as exc:
            abort(400, str(exc))

    @app.get("/galerija")
    @require_login
    def gallery_index():
        response.set_header("Cache-Control", "private, no-store")
        return render("gallery", "Galerija", albums=store.gallery_events(), album=None,
                      photos=[], csrf=token_for(current_user()))

    @app.get("/galerija/<event_id:int>")
    @require_login
    def gallery_album(event_id):
        album = store.event(event_id)
        if not album:
            raise HTTPError(404, "Dogodek ne obstaja.")
        response.set_header("Cache-Control", "private, no-store")
        return render("gallery", f"Galerija: {album['name']}", albums=[], album=album,
                      photos=store.photos(event_id), csrf=token_for(current_user()))

    @app.get("/galerija/slika/<photo_id:int>")
    @require_login
    def gallery_image(photo_id):
        photo = store.photo(photo_id)
        if not photo:
            raise HTTPError(404, "Fotografija ne obstaja.")
        image = static_file(photo["file_name"], root=str(photo_dir), mimetype="image/jpeg")
        image.set_header("Cache-Control", "private, no-store")
        image.set_header("X-Content-Type-Options", "nosniff")
        return image

    @app.post("/galerija/<event_id:int>/dodaj")
    @require_permission("admin")
    def gallery_upload(event_id):
        check_token()
        if not store.event(event_id):
            raise HTTPError(404, "Dogodek ne obstaja.")
        if store.photo_count(event_id) >= 100:
            abort(400, "Album ima lahko največ 100 fotografij.")
        caption = validate_text(request.forms.getunicode("caption"), 300, "Opis")
        alt_text = validate_text(request.forms.getunicode("alt_text"), 160, "Opis slike", required=True)
        try:
            normalized = normalize_photo(request.files.get("photo"))
        except CommunityValidationError as exc:
            abort(400, str(exc))
        photo_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.jpg"
        path = photo_dir / name
        with path.open("xb") as image_file:
            image_file.write(normalized)
        try:
            store.add_photo(event_id, name, caption, alt_text, current_user()["id"])
        except Exception:
            path.unlink(missing_ok=True)
            raise
        redirect(f"/galerija/{event_id}?sporocilo={quote_plus('Fotografija je dodana.')}")

    @app.post("/galerija/slika/<photo_id:int>/izbrisi")
    @require_permission("admin")
    def gallery_delete(photo_id):
        check_token()
        photo = store.photo(photo_id)
        if not photo:
            raise HTTPError(404, "Fotografija ne obstaja.")
        name = store.delete_photo(photo_id)
        if name:
            (photo_dir / name).unlink(missing_ok=True)
        redirect(f"/galerija/{photo['event_id']}?sporocilo={quote_plus('Fotografija je izbrisana.')}")

    @app.get("/klepet")
    @require_login
    def chat_page():
        response.set_header("Cache-Control", "private, no-store")
        return render("chat", "Klepet zbora", messages=store.messages(),
                      csrf=token_for(current_user()))

    @app.get("/api/klepet")
    @require_login
    def chat_history():
        response.content_type = "application/json; charset=utf-8"
        response.set_header("Cache-Control", "private, no-store")
        items = store.messages()
        return json.dumps([{
            "id": item["id"], "author_id": item["author_id"], "author": item["author"],
            "body": item["body"] if not item["deleted_at"] else "Sporočilo je izbrisano.",
            "created_at": item["created_at"].isoformat(),
            "edited": bool(item["edited_at"]), "deleted": bool(item["deleted_at"]),
        } for item in items], ensure_ascii=False)

    @app.post("/klepet")
    @require_login
    def chat_post():
        check_token()
        body = validate_text(request.forms.getunicode("body"), 2000, "Sporočilo", required=True)
        store.add_message(current_user()["id"], body)
        if on_message:
            try:
                on_message(current_user()["id"])
            except Exception:
                # Sending alerts must never lose an already saved message.
                pass
        redirect("/klepet")

    @app.post("/klepet/<message_id:int>/uredi")
    @require_login
    def chat_edit(message_id):
        check_token()
        body = validate_text(request.forms.getunicode("body"), 2000, "Sporočilo", required=True)
        if not store.edit_message(message_id, current_user()["id"], body):
            abort(403, "Urediš lahko samo svoje neizbrisano sporočilo.")
        redirect("/klepet")

    @app.post("/klepet/<message_id:int>/izbrisi")
    @require_login
    def chat_delete(message_id):
        check_token()
        admin = "admin" in set(current_user().get("permissions", [])) or bool(
            {"Predsednik", "Zborovodja"} & set(current_user()["roles"])
        )
        if not store.delete_message(message_id, current_user()["id"], admin):
            abort(403, "Sporočilo lahko izbriše avtor ali skrbnik.")
        redirect("/klepet")

    return store
