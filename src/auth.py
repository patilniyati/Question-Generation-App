import hashlib
import hmac
import re
import secrets
import sqlite3

from src.config import MIN_PASSWORD_LENGTH, PASSWORD_HASH_ITERATIONS
from src.database import create_user, get_user_by_email

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """Raised with a message that is safe to show to the user."""


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_HASH_ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt), expected_hash)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(name: str, email: str, password: str, confirm_password: str) -> dict:
    name = name.strip()
    email = normalize_email(email)

    if not name:
        raise AuthError("Please enter your name.")

    if not EMAIL_PATTERN.match(email):
        raise AuthError("Please enter a valid email address.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    if password != confirm_password:
        raise AuthError("Passwords do not match.")

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)

    try:
        user_id = create_user(name, email, password_hash, salt)
    except sqlite3.IntegrityError as error:
        raise AuthError("An account with this email already exists.") from error

    return {"id": user_id, "name": name, "email": email}


def authenticate_user(email: str, password: str) -> dict:
    email = normalize_email(email)
    user = get_user_by_email(email)

    # Same message for unknown email and wrong password, so accounts can't be probed.
    if not user or not verify_password(password, user["salt"], user["password_hash"]):
        raise AuthError("Incorrect email or password.")

    return {"id": user["id"], "name": user["name"], "email": user["email"]}
