# Autonomous AI DevOps Agent Platform

An end-to-end, self-hosted DevOps workspace for infrastructure generation, CI/CD analysis, incident diagnosis, and log-aware retrieval. The platform runs locally with FastAPI, Next.js, Redis, Ollama, SQLite, and a local vector store.

## Highlights

- Generate infrastructure for `docker_compose`, `kubernetes`, and `terraform`
- Analyze CI/CD pipelines for anti-patterns, score, and improvement suggestions
- Diagnose Kubernetes and Docker failures with remediation guidance
- Upload logs and query indexed operational context with RAG
- Keep projects, logs, pipelines, and agent runs scoped per user
- Run fully local with Ollama and graceful fallbacks when some AI dependencies are unavailable

## Architecture

```text
Next.js frontend
     |
     v
FastAPI backend
  |      |       |
  |      |       +-- Ollama
  |      |
  |      +---------- Redis
  |
  +----------------- SQLite + local vector store
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Pydantic v2, SQLAlchemy async |
| Auth | JWT bearer auth |
| Database | SQLite |
| Cache | Redis |
| Retrieval | FAISS with NumPy fallback |
| Local LLM | Ollama |
| State | Zustand |
| Testing | Pytest, ESLint, TypeScript, Next.js production build |
| Infra | Docker Compose, Kubernetes manifests |

## Repository Structure

```text
backend/              FastAPI app, agents, vector store, tests, seed data
frontend/             Next.js application
infra/docker/         Docker Compose stack
infra/scripts/        setup/dev/seed helper scripts
docs/                 supporting documentation
Makefile              top-level developer commands
LICENSE               MIT license
```

## Prerequisites

### Docker workflow

- Docker Desktop or Docker Engine with Compose support
- Recommended: 8 GB+ RAM if Ollama models will be pulled locally

### Local development workflow

- Python 3.12+
- Node.js 20+
- npm
- `uvicorn`
- Docker, if you want Redis and Ollama started by the helper script

## Quick Start

### Docker setup

```bash
make setup
```

This flow:

1. Creates `backend/.env` from `backend/.env.example` when missing
2. Builds and starts the Docker stack
3. Waits for backend health
4. Seeds a demo user, project, logs, pipeline, and vector data

Default URLs:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Demo account:

- Email: `demo@devops.ai`
- Password: `demo1234`

### If local ports are already in use

The setup flow supports custom host ports:

```bash
FRONTEND_PORT=3001 BACKEND_PORT=8001 make setup
```

Optional overrides supported by Docker setup:

- `FRONTEND_PORT`
- `BACKEND_PORT`
- `REDIS_PORT`
- `OLLAMA_PORT`

### Local development mode

```bash
make dev
```

This starts:

- Redis and Ollama via Docker
- FastAPI with hot reload
- Next.js dev server

If you also want demo data:

```bash
make seed
```

## Common Commands

```bash
make help
make setup
make dev
make up
make down
make logs
make seed
make test
make test-frontend
make clean
```

## Environment Variables

### Root `.env.example`

Used by Docker-oriented setup for shared secrets:

```env
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
```

### Backend `backend/.env.example`

```env
DATABASE_URL=sqlite+aiosqlite:///./devops_agent.db
REDIS_URL=redis://localhost:6379/0
OLLAMA_URL=http://localhost:11434
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OLLAMA_MODEL=llama3
OLLAMA_CODE_MODEL=codellama
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_STORE_PATH=./faiss_index
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend runtime variables

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`

## Core Features

### Authentication

- User registration
- Login with bearer token response
- Current-user profile endpoint

### Projects

- Create, list, update, and delete projects
- Scope logs, pipelines, and agent runs to owned projects

### Agents

- `infra`: infrastructure config generation
- `pipeline`: pipeline analyze, validate, and generate
- `heal`: Kubernetes and Docker troubleshooting
- `orchestrator`: backend multi-step workflow coordination

### Logs and RAG

- Upload text logs
- Upload `.log`, `.txt`, or `.json` files
- Index bundled DevOps knowledge
- Query indexed context with project-scoped retrieval

## Main API Endpoints

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Projects

- `POST /api/v1/projects/`
- `GET /api/v1/projects/`
- `GET /api/v1/projects/{project_id}`
- `PUT /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`

### Agents

- `POST /api/v1/agents/run`
- `POST /api/v1/agents/multi-run`
- `POST /api/v1/agents/auto-diagnose`
- `WS /api/v1/agents/ws/stream/{agent_type}`

### Pipelines

- `POST /api/v1/pipelines/`
- `GET /api/v1/pipelines/project/{project_id}`
- `POST /api/v1/pipelines/analyze`
- `POST /api/v1/pipelines/validate`
- `POST /api/v1/pipelines/generate`

### Logs and RAG

- `POST /api/v1/logs/`
- `GET /api/v1/logs/project/{project_id}`
- `POST /api/v1/logs/upload`
- `POST /api/v1/logs/upload-file`
- `POST /api/v1/logs/rag/query`
- `GET /api/v1/logs/rag/stats?project_id=...`
- `POST /api/v1/logs/rag/index-docs?project_id=...`

### Health

- `GET /health`

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

## Verification

The current repo passes:

```bash
cd backend && python -m pytest tests/ -q
cd frontend && npm run type-check
cd frontend && npm run lint
cd frontend && npm run build
```

## Seeded Demo Data

The seed script creates:

- Admin user `demo@devops.ai`
- A sample project
- A sample pipeline
- Sample Kubernetes log content
- Sample agent run history
- Indexed DevOps knowledge

## Notes

- The vector store uses FAISS when available and falls back to NumPy-based similarity search otherwise.
- RAG retrieval is project-scoped so one project's indexed logs do not leak into another project's results.
- Ollama model download can make first startup slower.
- Pipeline validation depends on `PyYAML`.
- SQLite is used for simple local development and demo workflows.

## Troubleshooting

### `make setup` fails because a port is already in use

Retry with overrides:

```bash
FRONTEND_PORT=3001 make setup
```

or:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=3001 make setup
```

### Frontend loads but backend calls fail

Check:

- backend health at `http://localhost:8000/health`
- `backend/.env`
- `NEXT_PUBLIC_API_URL`

### RAG returns no useful results

Make sure you have:

- uploaded logs, or
- run `make seed`, or
- indexed sample docs through `/api/v1/logs/rag/index-docs`

### Demo login does not work

Run:

```bash
make seed
```

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for the full text.

---
*Autonomous AI DevOps Agent Platform - v1.0.0-alpha*
