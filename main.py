import os

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates

import db

app = FastAPI()
templates = Jinja2Templates(directory="templates")
APP_ENV = os.environ.get("APP_ENV", "development")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def checkin_page(request: Request, conn=Depends(db.get_db)):
    people = db.list_people(conn)
    return templates.TemplateResponse(
        request, "checkin.html", {"people": people, "app_env": APP_ENV}
    )
