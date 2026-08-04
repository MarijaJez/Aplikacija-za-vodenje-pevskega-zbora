import json
import os
import uuid
from datetime import timedelta, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import quote_plus, urlencode

from bottle import Bottle, HTTPError, abort, redirect, request, response, static_file, template
from psycopg2 import IntegrityError

from Services.choir_service import ChoirService

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "Presentation" / "views"
STATIC = ROOT / "Presentation" / "static"
UPLOADS = ROOT / "uploads"
COOKIE_SECRET = os.getenv("COOKIE_SECRET", "zborissimo-local-development-secret-change-me")

app = Bottle()
service = ChoirService()
auth_service = service.auth


def current_user():
    raw_id = request.get_cookie("zbor_session", secret=COOKIE_SECRET)
    if not raw_id:
        return None
    try:
        return auth_service.get_user(int(raw_id))
    except (TypeError, ValueError):
        return None


def require_login(callback):
    @wraps(callback)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            redirect(f"/prijava?naprej={request.path}")
        if user["must_change_password"] and request.path != "/prva-prijava":
            redirect("/prva-prijava")
        return callback(*args, **kwargs)
    return wrapped


def require_permission(permission):
    def decorator(callback):
        @wraps(callback)
        @require_login
        def wrapped(*args, **kwargs):
            if permission not in auth_service.permissions(current_user()):
                abort(403, "Za to dejanje nimaš dovoljenja.")
            return callback(*args, **kwargs)
        return wrapped
    return decorator


def render(view, title, **context):
    user = current_user()
    permissions = auth_service.permissions(user)
    return template(
        "layout.tpl", template_lookup=[str(VIEWS)], view=f"{view}.tpl", title=title,
        active=view, json=json, current_user=user, permissions=permissions,
        message=request.query.getunicode("sporocilo") or "", **context,
    )


@app.get("/prijava")
def login_page():
    if current_user():
        redirect("/")
    return template("login.tpl", template_lookup=[str(VIEWS)], error=None)


@app.post("/prijava")
def login_submit():
    username = (request.forms.getunicode("username") or "").strip()
    password = request.forms.getunicode("password") or ""
    user = auth_service.authenticate(username, password)
    if not user:
        return template("login.tpl", template_lookup=[str(VIEWS)], error="Napačno uporabniško ime ali geslo.")
    response.set_cookie("zbor_session", str(user["id"]), secret=COOKIE_SECRET, httponly=True, samesite="lax", path="/")
    redirect("/prva-prijava" if user["must_change_password"] else "/")


@app.get("/odjava")
def logout():
    response.delete_cookie("zbor_session", path="/")
    redirect("/prijava")


@app.get("/prva-prijava")
@require_login
def first_login_page():
    user = current_user()
    return template("first_login.tpl", template_lookup=[str(VIEWS)], username=user["username"], error=None)


@app.post("/prva-prijava")
@require_login
def first_login_submit():
    user = current_user()
    password = request.forms.getunicode("password") or ""
    confirmation = request.forms.getunicode("confirmation") or ""
    try:
        auth_service.change_initial_password(user["id"], password, confirmation)
    except ValueError as error:
        return template("first_login.tpl", template_lookup=[str(VIEWS)], username=user["username"], error=str(error))
    redirect("/?sporocilo=Geslo je uspešno spremenjeno.")


@app.post("/spremeni-geslo")
@require_login
def change_own_password():
    new_password=request.forms.getunicode("new_password") or ""
    confirmation=request.forms.getunicode("confirmation") or ""
    try:
        auth_service.change_own_password(current_user()["id"],request.forms.getunicode("current_password") or "",new_password,confirmation)
    except ValueError as error:
        redirect(f"/?sporocilo={quote_plus(str(error))}")
    redirect("/?sporocilo=Geslo je uspešno spremenjeno.")


@app.get("/")
@require_login
def dashboard():
    return render("dashboard", "Nadzorna plošča", data=service.dashboard())


@app.get("/clani")
@require_login
def members():
    return render("members", "Člani zbora", members=service.members(), roles=service.roles(), selected_role=request.query.getunicode("vloga") or "")


@app.post("/clani")
@require_permission("admin")
def create_member():
    values={key:(request.forms.getunicode(key) or "").strip() for key in ("first_name","last_name","birth_date","email","phone","voice")}
    roles=request.forms.getall("roles")
    try:
        _,username=service.create_member(values,roles)
    except (IntegrityError, ValueError) as error:
        redirect("/clani?sporocilo=Člana ni bilo mogoče dodati; preveri vnesene podatke.")
    redirect(f"/clani?sporocilo=Član in račun {username} sta ustvarjena.")


@app.get("/clani/<member_id:int>")
@require_login
def member_detail(member_id):
    member = service.member(member_id)
    if not member:
        raise HTTPError(404, "Član ne obstaja")
    return render("member_detail", member["name"], member=member, events=service.events(), roles=service.roles())


@app.post("/clani/<member_id:int>/uredi")
@require_login
def update_member(member_id):
    user=current_user()
    values={key:(request.forms.getunicode(key) or "").strip() for key in ("first_name","last_name","birth_date","email","phone","voice")}
    try:
        service.update_member(user,member_id,values,request.forms.getall("roles"))
    except PermissionError as error:
        abort(403,str(error))
    except LookupError as error:
        abort(404,str(error))
    redirect(f"/clani/{member_id}?sporocilo=Podatki so shranjeni.")


@app.post("/clani/<member_id:int>/izbrisi")
@require_permission("admin")
def delete_member(member_id):
    try:
        service.delete_member(current_user(),member_id)
    except ValueError as error:
        abort(400,str(error))
    redirect("/clani?sporocilo=Član je izbrisan.")


@app.post("/clani/<member_id:int>/geslo")
@require_permission("admin")
def reset_password(member_id):
    username=auth_service.reset_password(member_id)
    redirect(f"/clani/{member_id}?sporocilo=Geslo za {username} je ponastavljeno.")


@app.get("/vloge")
@require_login
def roles():
    return render("roles", "Vloge v zboru", roles=service.roles())


@app.post("/vloge")
@require_permission("admin")
def create_role():
    service.create_role(request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/vloge?sporocilo=Vloga je dodana.")


@app.post("/vloge/<role_id:int>/izbrisi")
@require_permission("admin")
def delete_role(role_id):
    deleted=service.delete_role(role_id)
    redirect("/vloge?sporocilo="+("Vloga je izbrisana." if deleted else "Vloge ni mogoče izbrisati, ker jo uporablja vsaj en član."))


@app.post("/vloge/<role_id:int>/uredi")
@require_permission("admin")
def update_role(role_id):
    service.update_role(role_id,request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/vloge?sporocilo=Vloga je posodobljena.")


@app.get("/program")
@require_login
def songs():
    return render("songs", "Program zbora", songs=service.songs(), categories=service.categories())


@app.get("/kategorije")
@require_login
def categories():
    return render("categories", "Kategorije programa", categories=service.categories())


@app.post("/kategorije")
@require_permission("program")
def create_category():
    service.create_category(request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/kategorije?sporocilo=Kategorija je dodana.")


@app.post("/kategorije/<category_id:int>/uredi")
@require_permission("program")
def update_category(category_id):
    service.update_category(category_id,request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/kategorije?sporocilo=Kategorija je posodobljena.")


@app.post("/kategorije/<category_id:int>/izbrisi")
@require_permission("program")
def delete_category(category_id):
    deleted=service.delete_category(category_id)
    redirect("/kategorije?sporocilo="+("Kategorija je izbrisana." if deleted else "Kategorije ni mogoče izbrisati, ker jo uporablja vsaj ena pesem."))


def save_upload(upload, allowed, error_message):
    if not upload or not upload.filename: return None
    suffix=Path(upload.filename).suffix.lower()
    if suffix not in allowed: abort(400,error_message)
    UPLOADS.mkdir(exist_ok=True); filename=f"{uuid.uuid4().hex}{suffix}"; upload.save(str(UPLOADS / filename)); return filename


def song_uploads():
    return {
        "notes_path":save_upload(request.files.get("notes"),{".pdf",".jpg",".jpeg",".png"},"Dovoljene so datoteke PDF, JPG, JPEG in PNG."),
        "audio_path":save_upload(request.files.get("audio"),{".mp3",".wav",".m4a",".ogg"},"Dovoljeni so zvočni posnetki MP3, WAV, M4A in OGG."),
    }


@app.post("/program")
@require_permission("program")
def create_song():
    song_id=service.create_song({"title":request.forms.getunicode("title"),"author":request.forms.getunicode("author"),**song_uploads()},request.forms.getall("categories"))
    redirect(f"/program/{song_id}?sporocilo=Pesem je dodana.")


@app.post("/program/<song_id:int>/izbrisi")
@require_permission("program")
def delete_song(song_id):
    service.delete_song(song_id); redirect("/program?sporocilo=Pesem je izbrisana.")


@app.get("/program/<song_id:int>")
@require_login
def song_detail(song_id):
    song = service.song(song_id, current_user()["person_id"])
    if not song:
        raise HTTPError(404, "Pesem ne obstaja")
    return render("song_detail", song["title"], song=song, categories=service.categories(), conductor=auth_service.is_conductor(current_user()))


@app.post("/program/<song_id:int>/uredi")
@require_permission("program")
def update_song(song_id):
    service.update_song(song_id,{"title":request.forms.getunicode("title"),"author":request.forms.getunicode("author"),**song_uploads()},request.forms.getall("categories"))
    redirect(f"/program/{song_id}?sporocilo=Pesem je posodobljena.")


@app.post("/program/<song_id:int>/ocena")
@require_login
def save_review(song_id):
    rating=int(request.forms.get("rating") or 0)
    try:
        service.save_review(current_user()["person_id"],song_id,rating,request.forms.getunicode("comment") or "")
    except ValueError as error:
        abort(400,str(error))
    redirect(f"/program/{song_id}?sporocilo=Ocena in komentar sta shranjena.")


@app.get("/dogodki")
@require_login
def events():
    return render("events", "Vaje in dogodki", events=service.events(), songs=service.songs(), categories=service.categories(), event_types=service.event_types())


def ics_escape(value):
    return str(value or "").replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\n","\\n")


@app.get("/dogodki/koledar.ics")
@require_login
def events_calendar():
    lines=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Upravljanje zbora//SL","CALSCALE:GREGORIAN"]
    for event in service.calendar_events():
        start=event["event_date"].astimezone(timezone.utc); end=start+timedelta(hours=2)
        lines.extend(["BEGIN:VEVENT",f"UID:dogodek-{event['id']}@upravljanje-zbora.local",f"DTSTAMP:{start.strftime('%Y%m%dT%H%M%SZ')}",f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",f"SUMMARY:{ics_escape(event['name'])}",f"LOCATION:{ics_escape(event['place'])}",f"DESCRIPTION:{ics_escape(event['event_type'])}","END:VEVENT"])
    lines.append("END:VCALENDAR"); response.content_type="text/calendar; charset=utf-8"; response.set_header("Content-Disposition","attachment; filename=dogodki-zbora.ics"); return "\r\n".join(lines)+"\r\n"


@app.post("/dogodki")
@require_permission("admin")
def create_event():
    event_id=service.create_event({"event_date":request.forms.get("event_date"),"event_type":request.forms.getunicode("event_type"),"name":request.forms.getunicode("name"),"place":request.forms.getunicode("place")},[int(value) for value in request.forms.getall("songs")])
    redirect(f"/dogodki/{event_id}?sporocilo=Dogodek je dodan.")


@app.post("/dogodki/<event_id:int>/izbrisi")
@require_permission("admin")
def delete_event(event_id):
    service.delete_event(event_id); redirect("/dogodki?sporocilo=Dogodek je izbrisan.")


@app.get("/dogodki/<event_id:int>")
@require_login
def event_detail(event_id):
    event = service.event(event_id)
    if not event:
        raise HTTPError(404, "Dogodek ne obstaja")
    start=event["event_date"].astimezone(timezone.utc); end=start+timedelta(hours=2)
    google_url="https://calendar.google.com/calendar/render?"+urlencode({"action":"TEMPLATE","text":event["name"],"dates":f"{start.strftime('%Y%m%dT%H%M%SZ')}/{end.strftime('%Y%m%dT%H%M%SZ')}","location":event["place"],"details":event["event_type"]})
    return render("event_detail", event["title"], event=event, attendance_summary=service.event_attendance(event_id), songs=service.songs(), categories=service.categories(), event_types=service.event_types(), conductor=auth_service.is_conductor(current_user()), google_url=google_url)


@app.post("/dogodki/<event_id:int>/uredi")
@require_permission("admin")
def update_event(event_id):
    service.update_event(event_id,{"event_date":request.forms.get("event_date"),"event_type":request.forms.getunicode("event_type"),"name":request.forms.getunicode("name"),"place":request.forms.getunicode("place")},[int(value) for value in request.forms.getall("songs")])
    redirect(f"/dogodki/{event_id}?sporocilo=Dogodek je posodobljen.")


@app.post("/dogodki/<event_id:int>/program/<song_id:int>")
@require_login
def update_performance(event_id,song_id):
    rating=int(request.forms.get("rating") or 0)
    try:
        service.update_performance(current_user(),event_id,song_id,rating,request.forms.getunicode("comment") or "")
    except PermissionError as error:
        abort(403,str(error))
    except ValueError as error:
        abort(400,str(error))
    redirect(f"/dogodki/{event_id}?sporocilo=Ocena izvedbe je shranjena.")


@app.get("/prisotnost")
@require_login
def attendance():
    return render("attendance", "Prisotnost", data=service.attendance(request.query.get("leto"),request.query.getunicode("vrsta") or "Vse"))


@app.post("/api/prisotnost")
@require_login
def save_attendance():
    payload=request.json or {}
    try:
        service.save_attendance(current_user(),int(payload["event_id"]),int(payload["person_id"]),str(payload.get("status") or ""))
    except PermissionError as error:
        abort(403,str(error))
    except (KeyError,TypeError,ValueError) as error:
        abort(400,str(error))
    response.content_type="application/json"
    return {"ok":True}


@app.get("/blagajna")
@require_login
def treasury():
    return render("treasury", "Blagajna zbora", data=service.treasury())


@app.post("/blagajna")
@require_permission("treasury")
def create_transaction():
    service.create_transaction({"date":request.forms.get("date"),"description":request.forms.getunicode("description"),"person_name":request.forms.getunicode("person_name"),"kind":request.forms.get("kind"),"amount":request.forms.get("amount"),"settled":bool(request.forms.get("settled"))},current_user()["id"])
    redirect("/blagajna?sporocilo=Transakcija je shranjena.")


@app.post("/blagajna/<transaction_id:int>/poravnano")
@require_permission("treasury")
def toggle_transaction(transaction_id):
    service.set_transaction_settled(transaction_id,bool(request.forms.get("settled")))
    redirect("/blagajna?sporocilo=Status transakcije je posodobljen.")


@app.post("/blagajna/<transaction_id:int>/uredi")
@require_permission("treasury")
def update_transaction(transaction_id):
    service.update_transaction(transaction_id,{"date":request.forms.get("date"),"description":request.forms.getunicode("description"),"person_name":request.forms.getunicode("person_name"),"kind":request.forms.get("kind"),"amount":request.forms.get("amount"),"settled":bool(request.forms.get("settled"))})
    redirect("/blagajna?sporocilo=Transakcija je posodobljena.")


@app.get("/uploads/<filepath:path>")
@require_login
def uploaded_file(filepath):
    return static_file(filepath, root=str(UPLOADS))


@app.get("/static/<filepath:path>")
def assets(filepath):
    return static_file(filepath, root=str(STATIC))


if __name__ == "__main__":
    app.run(host=os.getenv("APP_HOST","127.0.0.1"),port=int(os.getenv("APP_PORT","8091")),debug=os.getenv("APP_DEBUG","true").lower()=="true",reloader=True)
