# CodeRunr

![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FAandALabs%2FCodeRunr%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)

A code execution sandbox that compiles and runs user-submitted code in secure, isolated environments using [Isolate](https://github.com/ioi/isolate).

We use isolate (A sandbox for securely executing untrusted programs) to execute program in isolated
environment using linux feature such as CgroupV2, namespace. The current version of the isolate uses linux cgroupV2, and it highly recommended to use cgroupV2.

## Supported Languages

Currently we are only supporting these languages, we will add more in future.

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

## Authentication

All API endpoints except docs, OpenAPI, and health require an API token.

Set `AUTH_TOKEN` in your `.env` file and send it on each protected request using either:

```bash
X-API-Key: <your-auth-token>
```

## API Endpoints

| Method | Endpoint                   | Description              |
| ------ | -------------------------- | ------------------------ |
| `GET`  | `/api/v1/health`           | Health check             |
| `POST` | `/api/v1/submissions`      | Create a submission      |
| `GET`  | `/api/v1/submissions/{id}` | Get submission result    |
| `GET`  | `/api/v1/languages`        | List supported languages |
| `POST` | `/api/v1/languages`        | Add a language           |
