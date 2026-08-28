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
