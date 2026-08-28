import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def get_db():
    with psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row) as conn:
        yield conn


def list_people(conn):
    return conn.execute(
        "SELECT id, full_name FROM people WHERE merged_into IS NULL ORDER BY full_name"
    ).fetchall()


def search_people(conn, q):
    return conn.execute(
        """
        SELECT id, full_name FROM people
        WHERE merged_into IS NULL AND word_similarity(%(q)s, full_name) > 0.3
        ORDER BY word_similarity(%(q)s, full_name) DESC
        LIMIT 8
        """,
        {"q": q},
    ).fetchall()


def get_admin_by_email(conn, email):
    return conn.execute(
        "SELECT id, email, password_hash FROM admins WHERE email = %(email)s",
        {"email": email},
    ).fetchone()


def get_person(conn, person_id):
    return conn.execute(
        "SELECT id, full_name FROM people WHERE id = %(id)s",
        {"id": person_id},
    ).fetchone()


def get_or_create_todays_session(conn):
    row = conn.execute(
        """
        INSERT INTO sessions (held_at) VALUES (now())
        ON CONFLICT (((held_at at time zone 'America/New_York')::date))
        DO UPDATE SET held_at = sessions.held_at
        RETURNING id
        """
    ).fetchone()
    return row["id"]


def check_in_person(conn, person_id, session_id):
    row = conn.execute(
        """
        INSERT INTO check_ins (person_id, session_id) VALUES (%(person_id)s, %(session_id)s)
        ON CONFLICT (person_id, session_id) DO NOTHING
        RETURNING id
        """,
        {"person_id": person_id, "session_id": session_id},
    ).fetchone()
    return row["id"] if row else None


def create_person_and_check_in(conn, full_name, email, source):
    with conn.transaction():
        person = conn.execute(
            """
            INSERT INTO people (full_name, email, source)
            VALUES (%(full_name)s, %(email)s, %(source)s)
            RETURNING id, full_name
            """,
            {"full_name": full_name, "email": email or None, "source": source},
        ).fetchone()
        session_id = get_or_create_todays_session(conn)
        check_in_person(conn, person["id"], session_id)
    return person
