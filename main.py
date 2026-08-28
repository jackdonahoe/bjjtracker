import os
from urllib.parse import quote

import bcrypt
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import db

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
APP_ENV = os.environ.get("APP_ENV", "development")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SECRET_KEY"],
    https_only=APP_ENV != "development",
)


class NotAuthenticated(Exception):
    pass


@app.exception_handler(NotAuthenticated)
def redirect_to_login(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/admin/login", status_code=303)


def require_admin(request: Request):
    if not request.session.get("admin_id"):
        raise NotAuthenticated()

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


@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request, "admin_login.html", {"app_env": APP_ENV, "error": None}
    )


@app.post("/admin/login")
def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    conn=Depends(db.get_db),
):
    admin = db.get_admin_by_email(conn, email)
    valid = admin and bcrypt.checkpw(password.encode(), admin["password_hash"].encode())
    if not valid:
        return templates.TemplateResponse(
            request,
            "admin_login.html",
            {"app_env": APP_ENV, "error": "Wrong email or password"},
            status_code=401,
        )

    request.session["admin_id"] = admin["id"]
    return RedirectResponse("/admin/dashboard", status_code=303)


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)


@app.get("/admin/dashboard")
def admin_dashboard(request: Request, _=Depends(require_admin), conn=Depends(db.get_db)):
    funnel = db.retention_funnel(conn)
    quiet = db.gone_quiet(conn)
    return templates.TemplateResponse(
        request, "dashboard.html", {"funnel": funnel, "quiet": quiet, "app_env": APP_ENV}
    )


@app.get("/admin/tonight")
def admin_tonight(request: Request, _=Depends(require_admin), conn=Depends(db.get_db)):
    attendance = db.tonight_attendance(conn)
    return templates.TemplateResponse(
        request, "tonight.html", {"attendance": attendance, "app_env": APP_ENV}
    )
