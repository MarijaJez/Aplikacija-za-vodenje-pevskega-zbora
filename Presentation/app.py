import json
import os
import uuid
from datetime import timedelta, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import quote_plus

from bottle import Bottle, HTTPError, abort, redirect, request, response, static_file, template
from psycopg2 import IntegrityError

from Data.repository import ChoirRepository
from Services.auth_service import AuthService
from Services.choir_service import ChoirService
from Services.google_calendar import CALENDAR_SCOPE, CalendarError, CalendarNotConnected, GoogleCalendarService
from Services.google_oauth import GoogleOAuthClient, GoogleOAuthError

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "Presentation" / "views"
STATIC = ROOT / "Presentation" / "static"
UPLOADS = ROOT / "uploads"
COOKIE_SECRET = os.getenv("COOKIE_SECRET")
if not COOKIE_SECRET:
    raise RuntimeError("Nastavi COOKIE_SECRET za podpisovanje sej.")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8091").rstrip("/")
GOOGLE_LOGIN_REDIRECT_URI = os.getenv("GOOGLE_LOGIN_REDIRECT_URI", f"{APP_BASE_URL}/prijava/google/povratni-klic")
GOOGLE_CALENDAR_REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", f"{APP_BASE_URL}/nastavitve/google-koledar/povratni-klic")

app = Bottle()
repository = ChoirRepository()
service = ChoirService(repository)
auth_service = AuthService(repository)
google_oauth = GoogleOAuthClient()
calendar_service = GoogleCalendarService(repository)


def set_signed_cookie(name, value, **kwargs):
    response.set_cookie(
        name, value, secret=COOKIE_SECRET, httponly=True, samesite="lax",
        secure=COOKIE_SECURE, path="/", **kwargs,
    )


def set_session(user_id, method):
    set_signed_cookie("zbor_session", str(user_id))
    set_signed_cookie("zbor_auth_method", method)


def oauth_flow_cookie(name):
    raw = request.get_cookie(name, secret=COOKIE_SECRET)
    try:
        return json.loads(raw) if raw else None
    except (TypeError, ValueError):
        return None


def current_user():
    raw_id = request.get_cookie("zbor_session", secret=COOKIE_SECRET)
    if not raw_id:
        return None
    try:
        return repository.get_user_by_id(int(raw_id))
    except (TypeError, ValueError):
        return None


def permission_set(user):
    if not user:
        return set()
    roles = set(user["roles"])
    if roles & {"Predsednik", "Zborovodja"}:
        return {"admin", "program", "attendance", "treasury", "self"}
    permissions = {"self"}
    if "Notar" in roles:
        permissions.add("program")
    if "Blagajnik" in roles:
        permissions.add("treasury")
    if "Beleženje prisotnosti" in roles:
        permissions.add("attendance")
    return permissions


def is_conductor(user=None):
    return "Zborovodja" in (user or current_user())["roles"]


def require_login(callback):
    @wraps(callback)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            redirect(f"/prijava?naprej={request.path}")
        auth_method = request.get_cookie("zbor_auth_method", secret=COOKIE_SECRET)
        if user["must_change_password"] and auth_method != "google" and request.path != "/prva-prijava":
            redirect("/prva-prijava")
        return callback(*args, **kwargs)
    return wrapped


def require_permission(permission):
    def decorator(callback):
        @wraps(callback)
        @require_login
        def wrapped(*args, **kwargs):
            if permission not in permission_set(current_user()):
                abort(403, "Za to dejanje nimaš dovoljenja.")
            return callback(*args, **kwargs)
        return wrapped
    return decorator


def render(view, title, **context):
    user = current_user()
    permissions = permission_set(user)
    auth_method = request.get_cookie("zbor_auth_method", secret=COOKIE_SECRET) or "password"
    return template(
        "layout.tpl", template_lookup=[str(VIEWS)], view=f"{view}.tpl", title=title,
        active=view, json=json, current_user=user, permissions=permissions,
        auth_method=auth_method, message=request.query.getunicode("sporocilo") or "", **context,
    )


@app.get("/prijava")
def login_page():
    if current_user():
        redirect("/")
    return template(
        "login.tpl", template_lookup=[str(VIEWS)],
        error=request.query.getunicode("napaka") or None,
        google_configured=google_oauth.configured,
    )


@app.post("/prijava")
def login_submit():
    username = (request.forms.getunicode("username") or "").strip()
    password = request.forms.getunicode("password") or ""
    user = auth_service.authenticate(username, password)
    if not user:
        return template("login.tpl", template_lookup=[str(VIEWS)], error="Napačno uporabniško ime ali geslo.", google_configured=google_oauth.configured)
    set_session(user["id"], "password")
    redirect("/prva-prijava" if user["must_change_password"] else "/")


@app.get("/prijava/google")
def google_login_start():
    try:
        flow = google_oauth.new_flow_values()
        url = google_oauth.authorization_url(
            GOOGLE_LOGIN_REDIRECT_URI, ["openid", "email"], flow,
        )
    except GoogleOAuthError as error:
        redirect(f"/prijava?napaka={quote_plus(str(error))}")
    set_signed_cookie("zbor_google_login_flow", json.dumps(flow), max_age=600)
    redirect(url)


@app.get("/prijava/google/povratni-klic")
def google_login_callback():
    flow = oauth_flow_cookie("zbor_google_login_flow")
    response.delete_cookie("zbor_google_login_flow", path="/")
    if request.query.get("error"):
        redirect("/prijava?napaka=Google+prijava+je+bila+preklicana.")
    if not flow or request.query.get("state") != flow.get("state"):
        redirect("/prijava?napaka=Prijavna+zahteva+je+potekla.+Poskusi+znova.")
    try:
        tokens = google_oauth.exchange_code(request.query.get("code") or "", GOOGLE_LOGIN_REDIRECT_URI, flow["verifier"])
        claims = google_oauth.verify_identity(tokens["id_token"], flow["nonce"])
        user, reason = auth_service.authenticate_google(claims)
    except GoogleOAuthError as error:
        redirect(f"/prijava?napaka={quote_plus(str(error))}")
    except IntegrityError:
        redirect("/prijava?napaka=Google+račun+je+že+povezan+z+drugim+članom.")
    if not user:
        messages = {
            "member_missing": "Ta Google e-pošta še ni pripisana članu. Najprej naj te doda zborovodja ali skrbnik.",
            "email_mismatch": "E-pošta Google računa se ne ujema več z e-pošto člana. Obrni se na skrbnika.",
            "identity_conflict": "Ta članski račun je že povezan z drugim Google računom. Obrni se na skrbnika.",
            "unverified_email": "Google e-poštni naslov ni potrjen.",
            "invalid_identity": "Google identiteta ni veljavna.",
        }
        redirect(f"/prijava?napaka={quote_plus(messages.get(reason, 'Prijava ni uspela.'))}")
    set_session(user["id"], "google")
    redirect("/")


@app.get("/odjava")
def logout():
    response.delete_cookie("zbor_session", path="/")
    response.delete_cookie("zbor_auth_method", path="/")
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
        if password != confirmation:
            raise ValueError("Gesli se ne ujemata.")
        auth_service.change_password(user["id"], password)
    except ValueError as error:
        return template("first_login.tpl", template_lookup=[str(VIEWS)], username=user["username"], error=str(error))
    redirect("/?sporocilo=Geslo je uspešno spremenjeno.")


@app.post("/spremeni-geslo")
@require_login
def change_own_password():
    new_password=request.forms.getunicode("new_password") or ""
    confirmation=request.forms.getunicode("confirmation") or ""
    try:
        if new_password != confirmation: raise ValueError("Novi gesli se ne ujemata.")
        auth_method = request.get_cookie("zbor_auth_method", secret=COOKIE_SECRET)
        if auth_method == "google":
            auth_service.change_password(current_user()["id"], new_password)
        else:
            auth_service.change_own_password(current_user()["id"],request.forms.getunicode("current_password") or "",new_password)
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
    except IntegrityError:
        redirect("/clani?sporocilo=E-poštni naslov ali uporabniško ime že uporablja drug član.")
    except ValueError as error:
        redirect(f"/clani?sporocilo={quote_plus(str(error))}")
    redirect(f"/clani?sporocilo=Član in račun {username} sta ustvarjena. Prijavi se lahko z dodanim Google računom.")


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
    if "admin" not in permission_set(user) and user["person_id"] != member_id: abort(403,"Urejaš lahko samo svoje podatke.")
    current=repository.get_member(member_id)
    if not current: abort(404)
    values={key:(request.forms.getunicode(key) or "").strip() for key in ("first_name","last_name","birth_date","email","phone","voice")}
    email_changed = current["email"].strip().lower() != values["email"].strip().lower()
    try:
        service.update_member(member_id,values)
    except IntegrityError:
        redirect(f"/clani/{member_id}?sporocilo=E-poštni naslov že uporablja drug član.")
    except ValueError as error:
        redirect(f"/clani/{member_id}?sporocilo={quote_plus(str(error))}")
    if "admin" in permission_set(user): repository.set_member_roles(member_id,request.forms.getall("roles"))
    message = "Podatki so shranjeni. Zaradi spremembe e-pošte je Google račun odvezan in se bo ob naslednji prijavi povezal na novo." if email_changed else "Podatki so shranjeni."
    redirect(f"/clani/{member_id}?sporocilo={quote_plus(message)}")


@app.post("/clani/<member_id:int>/izbrisi")
@require_permission("admin")
def delete_member(member_id):
    if current_user()["person_id"] == member_id: abort(400,"Svojega računa ne moreš izbrisati.")
    repository.delete_member(member_id); redirect("/clani?sporocilo=Član je izbrisan.")


@app.get("/vloge")
@require_login
def roles():
    return render("roles", "Vloge v zboru", roles=service.roles())


@app.post("/vloge")
@require_permission("admin")
def create_role():
    repository.create_role(request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/vloge?sporocilo=Vloga je dodana.")


@app.post("/vloge/<role_id:int>/izbrisi")
@require_permission("admin")
def delete_role(role_id):
    deleted=repository.delete_role(role_id)
    redirect("/vloge?sporocilo="+("Vloga je izbrisana." if deleted else "Vloge ni mogoče izbrisati, ker jo uporablja vsaj en član."))


@app.post("/vloge/<role_id:int>/uredi")
@require_permission("admin")
def update_role(role_id):
    repository.update_role(role_id,request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/vloge?sporocilo=Vloga je posodobljena.")


@app.get("/program")
@require_login
def songs():
    return render("songs", "Program zbora", songs=service.songs(), categories=repository.list_categories())


@app.get("/kategorije")
@require_login
def categories():
    return render("categories", "Kategorije programa", categories=repository.list_categories())


@app.post("/kategorije")
@require_permission("program")
def create_category():
    repository.create_category(request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/kategorije?sporocilo=Kategorija je dodana.")


@app.post("/kategorije/<category_id:int>/uredi")
@require_permission("program")
def update_category(category_id):
    repository.update_category(category_id,request.forms.getunicode("name"),request.forms.getunicode("description") or "")
    redirect("/kategorije?sporocilo=Kategorija je posodobljena.")


@app.post("/kategorije/<category_id:int>/izbrisi")
@require_permission("program")
def delete_category(category_id):
    deleted=repository.delete_category(category_id)
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
    song_id=repository.create_song({"title":request.forms.getunicode("title"),"author":request.forms.getunicode("author"),**song_uploads()},request.forms.getall("categories"))
    redirect(f"/program/{song_id}?sporocilo=Pesem je dodana.")


@app.post("/program/<song_id:int>/izbrisi")
@require_permission("program")
def delete_song(song_id):
    repository.delete_song(song_id); redirect("/program?sporocilo=Pesem je izbrisana.")


@app.get("/program/<song_id:int>")
@require_login
def song_detail(song_id):
    song = service.song(song_id)
    if not song:
        raise HTTPError(404, "Pesem ne obstaja")
    song["my_review"]=next((review for review in song["reviews"] if review["person_id"]==current_user()["person_id"]),None)
    return render("song_detail", song["title"], song=song, categories=repository.list_categories(), conductor=is_conductor())


@app.post("/program/<song_id:int>/uredi")
@require_permission("program")
def update_song(song_id):
    repository.update_song(song_id,{"title":request.forms.getunicode("title"),"author":request.forms.getunicode("author"),**song_uploads()},request.forms.getall("categories"))
    redirect(f"/program/{song_id}?sporocilo=Pesem je posodobljena.")


@app.post("/program/<song_id:int>/ocena")
@require_login
def save_review(song_id):
    rating=int(request.forms.get("rating") or 0)
    if rating not in range(1,6):
        abort(400,"Ocena mora biti med 1 in 5.")
    repository.upsert_review(current_user()["person_id"],song_id,rating,request.forms.getunicode("comment") or "")
    redirect(f"/program/{song_id}?sporocilo=Ocena in komentar sta shranjena.")


@app.get("/dogodki")
@require_login
def events():
    connection = repository.get_calendar_connection()
    return render(
        "events", "Vaje in dogodki", events=service.events(), songs=service.songs(),
        categories=repository.list_categories(), event_types=repository.list_event_types(),
        calendar_connection=connection,
    )


@app.get("/nastavitve/google-koledar")
@require_permission("admin")
def calendar_settings():
    connection = repository.get_calendar_connection()
    calendars = []
    calendar_error = None
    if connection and connection.get("active") and calendar_service.configured:
        try:
            calendars = calendar_service.list_calendars()
        except CalendarError as error:
            calendar_error = str(error)
    return render(
        "calendar_settings", "Skupni Google Koledar",
        connection=connection, calendars=calendars,
        calendar_error=calendar_error, configured=calendar_service.configured,
    )


@app.get("/nastavitve/google-koledar/povezi")
@require_permission("admin")
def calendar_connect():
    if not calendar_service.configured:
        redirect("/nastavitve/google-koledar?sporocilo=Najprej+dopolni+Google+OAuth+konfiguracijo+na+strežniku.")
    flow = google_oauth.new_flow_values()
    try:
        url = google_oauth.authorization_url(
            GOOGLE_CALENDAR_REDIRECT_URI,
            ["openid", "email", CALENDAR_SCOPE], flow, offline=True,
        )
    except GoogleOAuthError as error:
        redirect(f"/nastavitve/google-koledar?sporocilo={quote_plus(str(error))}")
    set_signed_cookie("zbor_google_calendar_flow", json.dumps(flow), max_age=600)
    redirect(url)


@app.get("/nastavitve/google-koledar/povratni-klic")
@require_permission("admin")
def calendar_callback():
    flow = oauth_flow_cookie("zbor_google_calendar_flow")
    response.delete_cookie("zbor_google_calendar_flow", path="/")
    if request.query.get("error"):
        redirect("/nastavitve/google-koledar?sporocilo=Povezovanje+je+bilo+preklicano.")
    if not flow or request.query.get("state") != flow.get("state"):
        redirect("/nastavitve/google-koledar?sporocilo=Zahteva+je+potekla.+Začni+znova.")
    try:
        tokens = google_oauth.exchange_code(request.query.get("code") or "", GOOGLE_CALENDAR_REDIRECT_URI, flow["verifier"])
        claims = google_oauth.verify_identity(tokens["id_token"], flow["nonce"])
        if claims.get("email_verified") is not True:
            raise CalendarError("Google e-poštni naslov ni potrjen.")
        calendar_service.store_authorization(tokens, claims, current_user()["id"])
    except (GoogleOAuthError, CalendarError) as error:
        redirect(f"/nastavitve/google-koledar?sporocilo={quote_plus(str(error))}")
    redirect("/nastavitve/google-koledar?sporocilo=Google+račun+je+povezan.+Izberi+skupni+koledar.")


@app.post("/nastavitve/google-koledar/izberi")
@require_permission("admin")
def calendar_select():
    try:
        selected = calendar_service.select_calendar(request.forms.getunicode("calendar_id") or "")
        succeeded, failed = calendar_service.sync_all()
    except CalendarError as error:
        redirect(f"/nastavitve/google-koledar?sporocilo={quote_plus(str(error))}")
    message = f"Koledar {selected['name']} je izbran. Sinhronizirano: {succeeded}; napake: {failed}."
    redirect(f"/nastavitve/google-koledar?sporocilo={quote_plus(message)}")


@app.post("/nastavitve/google-koledar/sinhroniziraj")
@require_permission("admin")
def calendar_sync_all():
    try:
        succeeded, failed = calendar_service.sync_all()
    except CalendarError as error:
        redirect(f"/nastavitve/google-koledar?sporocilo={quote_plus(str(error))}")
    redirect(f"/nastavitve/google-koledar?sporocilo=Sinhronizirano:+{succeeded};+napake:+{failed}.")


@app.post("/nastavitve/google-koledar/prekini")
@require_permission("admin")
def calendar_disconnect():
    repository.disconnect_google_calendar()
    redirect("/nastavitve/google-koledar?sporocilo=Povezava+je+prekinjena.+Dogodki+v+Google+Koledarju+so+ostali+nespremenjeni.")


def ics_escape(value):
    return str(value or "").replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\n","\\n")


@app.get("/dogodki/koledar.ics")
@require_login
def events_calendar():
    lines=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Upravljanje zbora//SL","CALSCALE:GREGORIAN"]
    for event in repository.list_events():
        start=event["event_date"].astimezone(timezone.utc); end=start+timedelta(hours=2)
        lines.extend(["BEGIN:VEVENT",f"UID:dogodek-{event['id']}@upravljanje-zbora.local",f"DTSTAMP:{start.strftime('%Y%m%dT%H%M%SZ')}",f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",f"SUMMARY:{ics_escape(event['name'])}",f"LOCATION:{ics_escape(event['place'])}",f"DESCRIPTION:{ics_escape(event['event_type'])}","END:VEVENT"])
    lines.append("END:VCALENDAR"); response.content_type="text/calendar; charset=utf-8"; response.set_header("Content-Disposition","attachment; filename=dogodki-zbora.ics"); return "\r\n".join(lines)+"\r\n"


@app.post("/dogodki")
@require_permission("admin")
def create_event():
    event_id=repository.create_event({"event_date":request.forms.get("event_date"),"event_type":request.forms.getunicode("event_type"),"name":request.forms.getunicode("name"),"place":request.forms.getunicode("place")},[int(value) for value in request.forms.getall("songs")])
    try:
        calendar_service.sync_event(repository.get_event(event_id))
        message="Dogodek je dodan in sinhroniziran z Google Koledarjem."
    except CalendarNotConnected:
        message="Dogodek je dodan. Skupni Google Koledar še ni povezan."
    except CalendarError:
        message="Dogodek je dodan, sinhronizacija z Google Koledarjem pa ni uspela. Poskusi jo znova v nastavitvah."
    redirect(f"/dogodki/{event_id}?sporocilo={quote_plus(message)}")


@app.post("/dogodki/<event_id:int>/izbrisi")
@require_permission("admin")
def delete_event(event_id):
    try:
        calendar_service.delete_event(event_id)
    except CalendarError as error:
        redirect(f"/dogodki/{event_id}?sporocilo={quote_plus('Dogodek ni izbrisan: '+str(error))}")
    repository.delete_event(event_id)
    redirect("/dogodki?sporocilo=Dogodek je izbrisan. Če je bil povezan s skupnim koledarjem, je odstranjen tudi tam.")


@app.get("/dogodki/<event_id:int>")
@require_login
def event_detail(event_id):
    event = service.event(event_id)
    if not event:
        raise HTTPError(404, "Dogodek ne obstaja")
    return render("event_detail", event["title"], event=event, songs=service.songs(), members=service.members(), categories=repository.list_categories(), event_types=repository.list_event_types(), conductor=is_conductor())


@app.post("/dogodki/<event_id:int>/uredi")
@require_permission("admin")
def update_event(event_id):
    repository.update_event(event_id,{"event_date":request.forms.get("event_date"),"event_type":request.forms.getunicode("event_type"),"name":request.forms.getunicode("name"),"place":request.forms.getunicode("place")},[int(value) for value in request.forms.getall("songs")])
    try:
        calendar_service.sync_event(repository.get_event(event_id))
        message="Dogodek je posodobljen tudi v Google Koledarju."
    except CalendarNotConnected:
        message="Dogodek je posodobljen. Skupni Google Koledar ni povezan."
    except CalendarError:
        message="Dogodek je posodobljen, sinhronizacija z Google Koledarjem pa ni uspela."
    redirect(f"/dogodki/{event_id}?sporocilo={quote_plus(message)}")


@app.post("/dogodki/<event_id:int>/program/<song_id:int>")
@require_login
def update_performance(event_id,song_id):
    if not is_conductor(): abort(403,"Ocene izvedb lahko ureja samo zborovodja.")
    rating=int(request.forms.get("rating") or 0)
    if rating not in range(1,6): abort(400,"Ocena mora biti med 1 in 5.")
    repository.update_performance(event_id,song_id,rating,request.forms.getunicode("comment") or "")
    redirect(f"/dogodki/{event_id}?sporocilo=Ocena izvedbe je shranjena.")


@app.get("/prisotnost")
@require_login
def attendance():
    return render("attendance", "Prisotnost", data=service.attendance(request.query.get("leto"),request.query.getunicode("vrsta") or "Vse"))


@app.post("/api/prisotnost")
@require_permission("attendance")
def save_attendance():
    payload=request.json or {}
    status=payload.get("status")
    if status not in {"present","late_under","late_over","excused","absent"}:
        abort(400,"Neveljaven status.")
    repository.upsert_attendance(int(payload["event_id"]),int(payload["person_id"]),status,current_user()["id"])
    response.content_type="application/json"
    return {"ok":True}


@app.get("/blagajna")
@require_login
def treasury():
    return render("treasury", "Blagajna zbora", data=service.treasury())


@app.post("/blagajna")
@require_permission("treasury")
def create_transaction():
    repository.create_transaction({"date":request.forms.get("date"),"description":request.forms.getunicode("description"),"person_name":request.forms.getunicode("person_name"),"kind":request.forms.get("kind"),"amount":request.forms.get("amount"),"settled":bool(request.forms.get("settled"))},current_user()["id"])
    redirect("/blagajna?sporocilo=Transakcija je shranjena.")


@app.post("/blagajna/<transaction_id:int>/poravnano")
@require_permission("treasury")
def toggle_transaction(transaction_id):
    repository.set_transaction_settled(transaction_id,bool(request.forms.get("settled")))
    redirect("/blagajna?sporocilo=Status transakcije je posodobljen.")


@app.post("/blagajna/<transaction_id:int>/uredi")
@require_permission("treasury")
def update_transaction(transaction_id):
    repository.update_transaction(transaction_id,{"date":request.forms.get("date"),"description":request.forms.getunicode("description"),"person_name":request.forms.getunicode("person_name"),"kind":request.forms.get("kind"),"amount":request.forms.get("amount"),"settled":bool(request.forms.get("settled"))})
    redirect("/blagajna?sporocilo=Transakcija je posodobljena.")


@app.get("/uploads/<filepath:path>")
@require_login
def uploaded_file(filepath):
    return static_file(filepath, root=str(UPLOADS))


@app.get("/manifest.webmanifest")
def web_manifest():
    return static_file("manifest.webmanifest", root=str(STATIC), mimetype="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    response.set_header("Service-Worker-Allowed", "/")
    response.set_header("Cache-Control", "no-cache")
    return static_file("sw.js", root=str(STATIC), mimetype="application/javascript")


@app.get("/static/<filepath:path>")
def assets(filepath):
    return static_file(filepath, root=str(STATIC))


if __name__ == "__main__":
    debug = os.getenv("APP_DEBUG", "false").lower() == "true"
    app.run(host=os.getenv("APP_HOST", "127.0.0.1"), port=int(os.getenv("APP_PORT", "8091")), debug=debug, reloader=debug)
