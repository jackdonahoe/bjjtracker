import os
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
APP_ENV = os.environ.get("APP_ENV", "development")

SOURCES = [
    ("friend", "Friend or teammate"),
    ("social_media", "Social media"),
    ("tabling", "Tabling event"),
    ("class_announcement", "Class announcement"),
    ("other", "Other"),
]


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def checkin_page(request: Request, conn=Depends(db.get_db)):
    people = db.list_people(conn)
    return templates.TemplateResponse(
        request, "checkin.html", {"people": people, "app_env": APP_ENV}
    )


@app.get("/api/people/search")
def search_people(q: str = "", conn=Depends(db.get_db)):
    if not q:
        return []
    return db.search_people(conn, q)


@app.post("/checkin")
def checkin(person_id: str = Form(""), typed_name: str = Form(""), conn=Depends(db.get_db)):
    person = db.get_person(conn, int(person_id)) if person_id.isdigit() else None
    if person is None:
        return RedirectResponse(f"/new?name={quote(typed_name)}", status_code=303)

    session_id = db.get_or_create_todays_session(conn)
    new_checkin = db.check_in_person(conn, person["id"], session_id)
    already = new_checkin is None

    return RedirectResponse(
        f"/checked-in?name={quote(person['full_name'])}&already={already}",
        status_code=303,
    )


@app.get("/checked-in")
def checked_in_page(request: Request, name: str = "", already: bool = False):
    return templates.TemplateResponse(
        request, "checked_in.html", {"name": name, "already": already, "app_env": APP_ENV}
    )


@app.get("/new")
def new_person_page(request: Request, name: str = ""):
    return templates.TemplateResponse(
        request, "new_person.html", {"name": name, "sources": SOURCES, "app_env": APP_ENV}
    )


@app.post("/new")
def new_person(
    full_name: str = Form(...),
    email: str = Form(""),
    source: str = Form(...),
    conn=Depends(db.get_db),
):
    valid_sources = {value for value, _ in SOURCES}
    if source not in valid_sources:
        source = "other"

    person = db.create_person_and_check_in(conn, full_name.strip(), email.strip(), source)

    return RedirectResponse(
        f"/checked-in?name={quote(person['full_name'])}&already=False", status_code=303
    )
