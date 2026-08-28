# BJJ Tracker

Check-in app for the UWF BJJ Club. Members tap their name on a QR-coded
page at the door; the admin dashboard shows a retention funnel and a
"gone quiet" list IMLeagues doesn't provide.

## Stack

Python 3.12, FastAPI, Postgres 16 (raw SQL via psycopg3, no ORM), Jinja2
templates, vanilla JS for the autocomplete.

## Local setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

createdb bjjtracker
psql bjjtracker -f schema.sql

cp .env.example .env   # fill in DATABASE_URL / SECRET_KEY
python scripts/create_admin.py

uvicorn main:app --reload
```

## Deploying to Railway

One Railway project, two environments, so real member data and the
public recruiter-facing demo never touch the same database:

1. `railway login`, `railway init` (creates the `production` environment).
2. Add a second environment named `demo` in the Railway dashboard.
3. In each environment, add a Postgres plugin — this gives each one its
   own `DATABASE_URL`.
4. Set env vars per environment: `production` gets `APP_ENV=production`
   and a random `SECRET_KEY`; `demo` gets `APP_ENV=demo` and a different
   `SECRET_KEY`.
5. Connect this repo; Railway detects Python from `requirements.txt` and
   uses `Procfile` for the start command.
6. Apply the schema once per environment:
   `psql "$DATABASE_URL" -f schema.sql`
7. Seed **only** demo: `psql "$DEMO_DATABASE_URL" -f scripts/seed_demo.sql`
   (demo login is `demo@example.com` / `demo1234`).
8. Create the real admin for production:
   `railway run --environment production python scripts/create_admin.py`
9. Add a custom subdomain per environment under Networking, and point
   the door QR code at the production subdomain's `/`.
