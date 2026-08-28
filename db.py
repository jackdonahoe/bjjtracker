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


def retention_funnel(conn):
    return conn.execute(
        """
        WITH counts AS (
            SELECT p.id, p.source, COUNT(c.id) AS n
            FROM people p JOIN check_ins c ON c.person_id = p.id
            WHERE p.merged_into IS NULL
            GROUP BY p.id, p.source
        ), bucketed AS (
            SELECT source, CASE WHEN n >= 4 THEN '4+' ELSE n::text END AS bucket, COUNT(*) AS people
            FROM counts
            GROUP BY source, bucket
        )
        SELECT source, bucket, people
        FROM bucketed
        ORDER BY source, CASE WHEN bucket = '4+' THEN 4 ELSE bucket::int END
        """
    ).fetchall()


def gone_quiet(conn):
    return conn.execute(
        """
        SELECT p.id, p.full_name, p.email, MAX(c.checked_in) AS last_seen
        FROM people p JOIN check_ins c ON c.person_id = p.id
        WHERE p.merged_into IS NULL
        GROUP BY p.id, p.full_name, p.email
        HAVING MAX(c.checked_in) < now() - interval '21 days'
        ORDER BY last_seen ASC
        """
    ).fetchall()


def tonight_attendance(conn):
    return conn.execute(
        """
        SELECT p.full_name, p.email, c.checked_in
        FROM check_ins c
        JOIN people p ON p.id = c.person_id
        JOIN sessions s ON s.id = c.session_id
        WHERE (s.held_at AT TIME ZONE 'America/New_York')::date =
              (now() AT TIME ZONE 'America/New_York')::date
        ORDER BY p.full_name ASC
        """
    ).fetchall()


def list_sessions(conn):
    return conn.execute(
        """
        SELECT s.id, s.held_at, COUNT(c.id) AS attendance
        FROM sessions s
        LEFT JOIN check_ins c ON c.session_id = s.id
        GROUP BY s.id
        ORDER BY s.held_at DESC
        """
    ).fetchall()


def get_session(conn, session_id):
    return conn.execute(
        "SELECT id, held_at FROM sessions WHERE id = %(id)s",
        {"id": session_id},
    ).fetchone()


def session_attendance(conn, session_id):
    return conn.execute(
        """
        SELECT p.full_name, p.email
        FROM check_ins c
        JOIN people p ON p.id = c.person_id
        WHERE c.session_id = %(session_id)s
        ORDER BY p.full_name ASC
        """,
        {"session_id": session_id},
    ).fetchall()


ROSTER_SORT_COLUMNS = {
    "name": "full_name",
    "email": "email",
    "source": "source",
    "first_seen": "first_seen",
    "checkins": "checkins",
}


def list_roster(conn, sort, direction):
    column = ROSTER_SORT_COLUMNS.get(sort, "full_name")
    direction = "desc" if direction == "desc" else "asc"
    # column/direction come from a fixed allowlist above, never from raw
    # input, so it's safe to interpolate them - psycopg's %s placeholders
    # only work for values, not column names or ASC/DESC keywords.
    query = f"""
        SELECT p.id, p.full_name, p.email, p.source, p.first_seen, COUNT(c.id) AS checkins
        FROM people p
        LEFT JOIN check_ins c ON c.person_id = p.id
        WHERE p.merged_into IS NULL
        GROUP BY p.id
        ORDER BY {column} {direction}
    """
    return conn.execute(query).fetchall()


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
