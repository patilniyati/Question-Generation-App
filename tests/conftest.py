import pytest
from helpers import FakeUpload, make_question

from src import database


@pytest.fixture
def make_upload():
    return FakeUpload


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A fresh, empty SQLite database for each test (never touches data/)."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    return tmp_path / "test.db"


@pytest.fixture
def questions():
    return [make_question(i) for i in range(5)]
