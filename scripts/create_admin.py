import getpass
import os

import bcrypt
import psycopg
from dotenv import load_dotenv

load_dotenv()


def main():
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password: ")
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    database_url = os.environ["DATABASE_URL"]
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(
            "INSERT INTO admins (email, password_hash) VALUES (%(email)s, %(password_hash)s)",
            {"email": email, "password_hash": password_hash},
        )

    print(f"Created admin: {email}")


if __name__ == "__main__":
    main()
