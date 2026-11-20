import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

MAX_UPLOAD_MB = 20
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

CHUNK_SIZE = 3500
CHUNK_OVERLAP = 300

# Accounts and quiz history are stored in a local SQLite file.
DB_PATH = Path(os.getenv("MCQ_DB_PATH", BASE_DIR / "data" / "mcq_app.db"))

# Password hashing (PBKDF2-HMAC-SHA256).
PASSWORD_HASH_ITERATIONS = 240_000
MIN_PASSWORD_LENGTH = 8