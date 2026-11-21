import sqlite3
import time

import pytest
from helpers import make_question

from src.auth import register_user
from src.database import (
    delete_quiz,
    get_connection,
    init_db,
    list_quizzes,
    save_quiz,
)


@pytest.fixture
def jane(db):
    return register_user("Jane", "jane@school.edu", "password123", "password123")


@pytest.fixture
def john(db):
    return register_user("John", "john@school.edu", "password123", "password123")


def test_init_db_is_idempotent(db):
    init_db()
    init_db()


def test_save_and_list_roundtrip(jane, questions):
    quiz_id = save_quiz(jane["id"], "biology.pdf", "medium", "Photosynthesis", questions)

    [quiz] = list_quizzes(jane["id"])

    assert quiz["id"] == quiz_id
    assert quiz["title"] == "Photosynthesis"
    assert quiz["document_name"] == "biology.pdf"
    assert quiz["difficulty"] == "medium"
    assert quiz["questions"] == questions
    assert quiz["created_at"].tzinfo is not None


def test_title_falls_back_to_document_name_when_no_topic(jane, questions):
    save_quiz(jane["id"], "chapter3.docx", "easy", "   ", questions)

    assert list_quizzes(jane["id"])[0]["title"] == "chapter3.docx"


def test_questions_with_unicode_survive_roundtrip(jane):
    unicode_questions = [make_question(0, question="Qu'est-ce que la photosynthèse ? 光合作用")]
    save_quiz(jane["id"], "bio.txt", "easy", "", unicode_questions)

    assert list_quizzes(jane["id"])[0]["questions"] == unicode_questions


def test_history_is_newest_first(jane, questions):
    first = save_quiz(jane["id"], "a.txt", "easy", "First", questions)
    time.sleep(1.1)  # created_at has one-second resolution; id is only a tiebreak
    second = save_quiz(jane["id"], "b.txt", "easy", "Second", questions)

    assert [q["id"] for q in list_quizzes(jane["id"])] == [second, first]


def test_teachers_only_see_their_own_history(jane, john, questions):
    save_quiz(jane["id"], "jane.txt", "easy", "Jane's quiz", questions)

    assert len(list_quizzes(jane["id"])) == 1
    assert list_quizzes(john["id"]) == []


def test_delete_removes_quiz(jane, questions):
    quiz_id = save_quiz(jane["id"], "a.txt", "easy", "", questions)

    delete_quiz(jane["id"], quiz_id)

    assert list_quizzes(jane["id"]) == []


def test_teacher_cannot_delete_another_teachers_quiz(jane, john, questions):
    quiz_id = save_quiz(jane["id"], "a.txt", "easy", "", questions)

    delete_quiz(john["id"], quiz_id)

    assert len(list_quizzes(jane["id"])) == 1


def test_quiz_requires_an_existing_user(db, questions):
    with pytest.raises(sqlite3.IntegrityError):
        save_quiz(9999, "a.txt", "easy", "", questions)


def test_failed_transaction_is_rolled_back(db):
    with pytest.raises(RuntimeError):
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO users (name, email, password_hash, salt, created_at) "
                "VALUES ('x', 'x@x.co', 'h', 's', 'now')"
            )
            raise RuntimeError("boom")

    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 0
