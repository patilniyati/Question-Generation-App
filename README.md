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

## Features

**Available now**
- Upload PDF, DOCX or TXT (up to 20 MB) and generate 3-15 multiple-choice
  questions with a chosen difficulty and optional topic focus
- Each question includes the correct answer, an explanation and the supporting
  sentence from the document
- Automatic validation that rejects malformed questions
- Teacher accounts (sign up / sign in) with a private quiz history
- Download any quiz as a PDF: questions first, then a single answer-key page
- Colour-themed, responsive Streamlit UI

**Planned** (see the roadmap below)
- Questions drawn from the whole document, not just the first part
- Removal of near-duplicate questions
- Retries and timeouts when the AI service fails or is rate limited
- Postgres database with versioned migrations, so history survives redeploys
- Stay signed in after a refresh, password reset, or Google/Microsoft sign-in
- Login throttling and per-teacher daily quotas
- Docker image, CI checks and structured logging
- Optional: background generation for large documents, and a separate API

## Roadmap

The app is being moved to a modular, deployable structure in small phases. The
app keeps working after each phase.

| Phase | Goal | User-visible change |
|---|---|---|
| 0 | Safety net: tests, pinned dependencies, git hygiene | None (done) |
| 1 | Restructure into `src/mcqgen/` packages, typed config | None |
| 2 | Separate services and repositories from the UI | None |
| 3 | Better generation: all chunks, dedupe, retries | Better quizzes |
| 4 | Postgres, migrations, docker-compose | History survives redeploys |
| 5 | Production login: sessions, password reset or OIDC | Stay signed in |
| 6 | Docker, CI, logging, quotas | None |
| 7 | Optional: background jobs or API split | Only if needed |

Target structure after Phase 2:

```
src/mcqgen/
  config.py        typed settings from environment variables
  domain/          User, Quiz, Question dataclasses
  db/              engine and repositories (the only place with SQL)
  services/        auth, quiz generation, history (no Streamlit imports)
  infra/           llm/, documents/, exporters/
  ui/              Streamlit app, pages, components
```

Dependencies point one way: `ui -> services -> (db, infra) -> domain`.

## Known limitations

These are the gaps the roadmap addresses.

- Questions are generated from the first text chunk only, so long documents are
  only partly covered (Phase 3).
- No password reset, no login rate limiting, and a browser refresh signs you
  out (Phase 5).
- SQLite lives on local disk, so hosts that wipe the disk on redeploy lose all
  history (Phase 4).
- Scanned PDFs are not supported (no OCR).
- PDF export does not support non-Latin scripts such as Hindi.
- The validator crashes on a `null` option from the model (covered by an
  expected-failure test).
