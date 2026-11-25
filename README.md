# Smart Support Desk

A small support desk web app. Customers submit tickets, a scikit-learn model predicts
each ticket's category, rules set its priority, and an LLM drafts a reply using only
the FAQ. A logged-in team lists, filters and updates tickets.

## Quick start (Docker)

Requires Docker Desktop or Docker Engine with Compose.

macOS/Linux or Git Bash:

```bash
cp .env.example .env
docker compose up --build
```

Windows PowerShell:

```powershell
copy .env.example .env
docker compose up --build
```

Before using it beyond a local trial, edit `.env`:

| Variable | Purpose |
|---|---|
| `TEAM_USERNAME`, `TEAM_PASSWORD` | Team login |
| `SESSION_SECRET` | Signs the login cookie; use a long random value |
| `GEMINI_API_KEY` | Enables AI reply drafts; get a free key from Google AI Studio |

Without a valid Gemini key, the app still works and each ticket shows a clear fallback
instead of an AI draft. Optional: `GEMINI_MODEL` changes the model and `APP_PORT`
changes the local port (default `8000`).

## Pages

| URL | Purpose |
|---|---|
| http://localhost:8000/ | Customer support form |
| http://localhost:8000/team | Team ticket list (login required) |
| http://localhost:8000/docs | REST API documentation |
| http://localhost:8000/health | Health check |

Ticket data is stored in the `support-db` Docker volume, so it survives restarts.

## Local development

Requires Python 3.13.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\uvicorn app.main:app --reload
```

On macOS/Linux, use `.venv/bin/python` and `.venv/bin/uvicorn`, and `cp` instead of `copy`.

## Tests

```powershell
.venv\Scripts\python -m pytest -q
```

The tests run offline with a fake LLM and a temporary SQLite database.

## Retrain the classifier

```powershell
.venv\Scripts\python -m ml.explore
.venv\Scripts\python -m ml.prepare
.venv\Scripts\python -m ml.train
.venv\Scripts\python -m ml.evaluate
```

Retraining downloads the public Bitext dataset. Trained model is committed at
`models/classifier.joblib`, so running the app does not need the dataset.

`ml.evaluate` rewrites `ml/reports/my_20.md`, so keep a copy of any notes in that file first.

## Evaluate reply drafts

Put the test tickets in `eval/reply_test_tickets.json`, then run:

```powershell
.venv\Scripts\python -m eval.run_reply_eval
```

This calls the real LLM and writes `eval/reply_eval.md`. It will not replace an existing
report unless you pass `--force`.

## Reports

| File | Contents |
|---|---|
| `ml/reports/explore.md` | Dataset exploration |
| `ml/reports/split.md` | Cleaning, near-duplicate groups and leak check |
| `ml/reports/model.md` | Test-set results |
| `ml/reports/my_20.md` | Results on hand-written messages |
| `eval/reply_eval.md` | Reply draft evaluation |
| `NOTES.md` | Design choices, trade-offs and next steps |
