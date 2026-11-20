import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from src.config import DB_PATH


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                document_name TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                questions_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_quizzes_user
                ON quizzes (user_id, created_at DESC);
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- Users ----------


def create_user(name: str, email: str, password_hash: str, salt: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, salt, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, salt, _now()),
        )
        return cursor.lastrowid


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


# ---------- Quiz history ----------


def save_quiz(
    user_id: int,
    document_name: str,
    difficulty: str,
    topic: str,
    questions: list[dict],
) -> int:
    title = topic.strip() or document_name

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO quizzes "
            "(user_id, title, document_name, difficulty, topic, questions_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                title,
                document_name,
                difficulty,
                topic.strip(),
                json.dumps(questions, ensure_ascii=False),
                _now(),
            ),
        )
        return cursor.lastrowid


def _row_to_quiz(row: sqlite3.Row) -> dict:
    quiz = dict(row)
    quiz["questions"] = json.loads(quiz.pop("questions_json"))
    quiz["created_at"] = datetime.fromisoformat(quiz["created_at"]).astimezone()
    return quiz


def list_quizzes(user_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (user_id,),
        ).fetchall()
    return [_row_to_quiz(row) for row in rows]


def delete_quiz(user_id: int, quiz_id: int) -> None:
    # user_id is part of the filter so a teacher can only delete her own quizzes.
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM quizzes WHERE id = ? AND user_id = ?", (quiz_id, user_id)
        )
