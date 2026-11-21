import pytest

from src.auth import (
    AuthError,
    authenticate_user,
    hash_password,
    register_user,
    verify_password,
)
from src.database import get_user_by_email

GOOD = {"name": "Jane Smith", "email": "jane@school.edu", "password": "password123"}


def register(**overrides):
    data = {**GOOD, "confirm_password": GOOD["password"], **overrides}
    return register_user(
        data["name"], data["email"], data["password"], data["confirm_password"]
    )


def test_hash_is_deterministic_per_salt_and_differs_across_salts():
    salt_a, salt_b = "aa" * 16, "bb" * 16

    assert hash_password("secret", salt_a) == hash_password("secret", salt_a)
    assert hash_password("secret", salt_a) != hash_password("secret", salt_b)


def test_verify_password():
    salt = "cc" * 16
    stored = hash_password("secret", salt)

    assert verify_password("secret", salt, stored)
    assert not verify_password("Secret", salt, stored)


def test_register_returns_user_and_lowercases_email(db):
    user = register(email="  Jane@School.EDU ")

    assert user["email"] == "jane@school.edu"
    assert user["name"] == "Jane Smith"
    assert isinstance(user["id"], int)


def test_password_is_never_stored_in_plain_text(db):
    register()
    row = get_user_by_email("jane@school.edu")

    assert GOOD["password"] not in row.values()
    assert row["password_hash"] != GOOD["password"]
    assert len(row["salt"]) == 32


def test_two_users_with_same_password_get_different_hashes(db):
    register()
    register(email="john@school.edu", name="John")

    jane = get_user_by_email("jane@school.edu")
    john = get_user_by_email("john@school.edu")

    assert jane["salt"] != john["salt"]
    assert jane["password_hash"] != john["password_hash"]


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"name": "  "}, "enter your name"),
        ({"email": "not-an-email"}, "valid email"),
        ({"email": "a@b"}, "valid email"),
        ({"password": "short", "confirm_password": "short"}, "at least 8"),
        ({"confirm_password": "different123"}, "do not match"),
    ],
)
def test_register_validation_errors(db, overrides, message):
    with pytest.raises(AuthError, match=message):
        register(**overrides)


def test_duplicate_email_rejected_case_insensitively(db):
    register()

    with pytest.raises(AuthError, match="already exists"):
        register(email="JANE@school.edu")


def test_login_success(db):
    registered = register()

    assert authenticate_user("Jane@School.edu ", GOOD["password"]) == registered


def test_login_wrong_password(db):
    register()

    with pytest.raises(AuthError, match="Incorrect email or password"):
        authenticate_user(GOOD["email"], "wrong-password")


def test_login_unknown_email_gives_same_message_as_wrong_password(db):
    register()

    with pytest.raises(AuthError) as unknown:
        authenticate_user("nobody@school.edu", "whatever123")
    with pytest.raises(AuthError) as wrong:
        authenticate_user(GOOD["email"], "wrong-password")

    assert str(unknown.value) == str(wrong.value)


def test_login_result_never_contains_secrets(db):
    register()
    user = authenticate_user(GOOD["email"], GOOD["password"])

    assert set(user) == {"id", "name", "email"}
