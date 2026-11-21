# AI MCQ Generator

Upload a PDF, DOCX or TXT document and generate multiple-choice questions with
Groq. Teachers sign in, keep a history of their quizzes, and download each quiz
as a PDF (questions first, then a single answer-key page).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env               # then put your Groq key in .env
streamlit run app.py
```

Accounts and quiz history are stored in `data/mcq_app.db` (SQLite, created on
first run).

## Run the tests

```bash
pytest
```

No API key or network is needed: the Groq client is replaced by a fake in the
tests, and each test uses its own temporary database.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | (required) | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model used for generation |
| `MCQ_DB_PATH` | `data/mcq_app.db` | SQLite file location |

## Never commit

`.env` (your API key) and `data/` (teachers' accounts and quizzes) are listed in
`.gitignore`. Keep them there.

## Known limitations

- Questions are generated from the first text chunk only, so long documents are
  only partly covered.
- No password reset and no login rate limiting.
- Scanned PDFs are not supported (no OCR).
- The validator crashes on a `null` option from the model (covered by an
  expected-failure test).
