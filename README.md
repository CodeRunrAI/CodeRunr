# CodeRunr

A code execution sandbox service that compiles and runs user-submitted code in secure, isolated environments using [Isolate](https://github.com/ioi/isolate).

## Tech Stack

- **API** — FastAPI (Python 3.12+)
- **Task Queue** — Celery + Redis
- **Database** — PostgreSQL 16
- **Sandbox** — Isolate (cgroup v2)
- **Packaging** — uv, Docker

## Supported Languages

C, C++, Python, JavaScript, TypeScript, Java, Go, Rust

## Getting Started

### Prerequisites

- Docker & Docker Compose

### Run

```bash
docker compose up -d --build
```

The API will be available at `http://localhost:8080`.

- Docs — [http://localhost:8000/docs](http://localhost:8080/docs)
- Health — `GET /api/v1/health`

## API Endpoints

| Method | Endpoint                   | Description              |
| ------ | -------------------------- | ------------------------ |
| `GET`  | `/api/v1/health`           | Health check             |
| `POST` | `/api/v1/submissions`      | Create a submission      |
| `GET`  | `/api/v1/submissions/{id}` | Get submission result    |
| `GET`  | `/api/v1/languages`        | List supported languages |
| `POST` | `/api/v1/languages`        | Add a language           |
