# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --frozen

# Run all tests
pytest

# Run a single test file
pytest tests/path/to/test_file.py

# Run a single test
pytest tests/path/to/test_file.py::test_function_name

# Lint
ruff check .
ruff format .

# Apply database migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Seed supported languages
uv run python -m db.seeds.languages

# Start all services (API, worker, DB, Redis, LocalStack)
docker compose up --build

# Run API server directly
uvicorn main:app --host 0.0.0.0 --port 8000

# Run Celery worker directly
celery -A worker.celery worker --loglevel=info
```

## Architecture

CodeRunr is a code execution sandbox API. Untrusted code is compiled and run inside **Isolate** (a Linux sandboxer using CgroupV2 + namespaces). The system has three runtime components:

### 1. API Server (`main.py`)
FastAPI app with routes under `/api/v1/`. Receives submission requests, writes a `Submission` record to PostgreSQL with `status=Queued`, then enqueues a Celery task. Clients poll the submission endpoint or receive results via webhook callback. Authentication is via `X-API-Key` header (`utils/security.py`).

### 2. Task Queue (`worker/`)
Celery with AWS SQS as the broker and PostgreSQL as the result backend. The main task is `submit_submission_task` in `worker/tasks.py`. It retrieves the submission by token, delegates to the sandbox, then writes execution results back to the DB. If `webhook_url` was provided, it POSTs the result via HTTPX.

### 3. Code Sandbox (`sandbox/isolate.py`)
`IsolateCodeSandbox` wraps the `isolate` CLI binary. For each submission: init box → compile (if language has a compile command) → run with limits → parse stdout/stderr/metadata → cleanup. Resource constraints (CPU time, wall time, memory, stack, file size, process count) are passed per-submission and enforced by Isolate.

### Data Flow
```
Client → POST /submissions → API creates Submission(Queued) → enqueue Celery task
  → Worker picks up task → IsolateCodeSandbox executes code
  → Worker updates Submission(Accepted|TimeLimitExceeded|…) → optional webhook POST
  → Client polls GET /submissions/{token}
```

### Key Directories
| Path | Purpose |
|------|---------|
| `config/` | Pydantic settings: app, AWS, Celery, sandbox, logging |
| `db/` | SQLAlchemy models, async/sync repositories, Alembic migrations, seeds |
| `routes/` | FastAPI route handlers (submissions, languages) |
| `schema/` | Pydantic request/response schemas |
| `sandbox/` | Isolate integration and execution logic |
| `worker/` | Celery app initialization and task definitions |
| `utils/` | API key security, async HTTP client helpers |
| `exceptions/` | Error-handling decorators for routes |
| `tests/` | pytest suite; uses `aiosqlite` in-memory DB for isolation |

### Deployment Targets
- **Docker Compose** — local dev; see `docker-compose.yml`. Worker container runs Ubuntu 24.04 with `isolate` v2.2 and all language compilers; it must be `privileged` and cgroup-aware.
- **AWS Lambda** — `lambda_handler.py` wraps the FastAPI app with Mangum and runs Alembic migrations + language seeding on cold start.

### Database
PostgreSQL (async via AsyncPG for the API, sync psycopg2 for Celery). Three main tables: `languages`, `submissions`, `submission_batches`. Migrations live in `db/alembic/`.

### Environment
Configured via `.env` / environment variables parsed by Pydantic `BaseSettings` in `config/`. AWS credentials, DB URL, Redis URL, and API keys are the critical values. `config/aws.py` constructs the SQS broker URL consumed by Celery.
