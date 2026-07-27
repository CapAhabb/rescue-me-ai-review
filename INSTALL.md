# Install And Run

Rescue Me has two reviewable surfaces:

- Static web console in `frontend/web`
- Python backend in `backend`

The current backend uses only the Python standard library and SQLite. No API
keys or external services are required for local review.

## Requirements

- Python 3.11 or newer
- Docker Desktop or Docker Engine, optional

## Run The Web Console

```bash
python3 -m http.server 4173 -d frontend/web
```

Open:

```text
http://127.0.0.1:4173/
```

## Run The Backend

```bash
python3 backend/run_backend.py
```

The backend listens on:

```text
http://127.0.0.1:8088
```

## Run Tests

```bash
python3 -m unittest discover -s backend/tests
python3 -m py_compile backend/rescue_me/*.py backend/run_backend.py
```

## Docker

Run the backend and frontend together:

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:4173/
http://127.0.0.1:8088/
```

