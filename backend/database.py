import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).parent / "study_groups.db"


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                topic TEXT NOT NULL,
                location TEXT NOT NULL,
                max_participants INTEGER NOT NULL
                    CHECK (max_participants BETWEEN 1 AND 50)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS memberships (
                student_id INTEGER NOT NULL,
                session_id INTEGER NOT NULL,
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (student_id, session_id),

                FOREIGN KEY (student_id)
                    REFERENCES students(id) ON DELETE CASCADE,

                FOREIGN KEY (session_id)
                    REFERENCES study_sessions(id) ON DELETE CASCADE
            )
        """)


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")