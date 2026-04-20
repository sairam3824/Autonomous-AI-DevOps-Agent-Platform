# API Documentation

Base URL: `http://localhost:8000`

## Authentication

All endpoints except `/health`, `/api/v1/auth/register`, and `/api/v1/auth/login` require a Bearer token.

```
Authorization: Bearer <token>
```

### POST /api/v1/auth/register
Create a new user account.

**Request:**
```json
{"email": "user@example.com", "username": "johndoe", "password": "secret123"}
```

**Response (201):**
```json
{"access_token": "eyJ...", "token_type": "bearer", "user": {"id": 1, "email": "user@example.com", "username": "johndoe", "role": "engineer", "is_active": true, "created_at": "..."}}
```

### POST /api/v1/auth/login
```json
{"email": "demo@devops.ai", "password": "demo1234"}
```

### GET /api/v1/auth/me
Returns the current authenticated user.

---

## Agents

### POST /api/v1/agents/run
Execute a single agent.

**Request:**
```json
{
  "agent_type": "heal",
  "input_data": {"logs": "CrashLoopBackOff in pod web-app-xyz"},
  "project_id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "agent_type": "heal",
  "status": "completed",
  "output_data": {"diagnosis": [...], "summary": "..."},
  "execution_time_ms": 1250,
  "created_at": "..."
}
```

### POST /api/v1/agents/multi-run
Run multiple agents sequentially or in parallel.

```json
{
  "agents": [
    {"agent_type": "heal", "input_data": {"logs": "..."}},
    {"agent_type": "pipeline", "input_data": {"action": "analyze", "yaml_content": "..."}}
  ],
  "mode": "sequential"
}
```

### POST /api/v1/agents/auto-diagnose
Multi-agent workflow: heal -> pipeline -> infra.

### WS /api/v1/agents/ws/stream/{agent_type}
WebSocket endpoint for streaming agent execution events.

---

## Projects

### POST /api/v1/projects/
```json
{"name": "My Project", "description": "...", "repo_url": "https://github.com/..."}
```

### GET /api/v1/projects/
List all projects for the current user.

### GET /api/v1/projects/{id}
### PUT /api/v1/projects/{id}
### DELETE /api/v1/projects/{id}

---

## Pipelines

### POST /api/v1/pipelines/
Create a pipeline record.

### GET /api/v1/pipelines/project/{id}
List pipelines for a project.

### POST /api/v1/pipelines/analyze
```json
{"yaml_content": "name: CI\non: [push]\n...", "platform": "github_actions"}
```

**Response:**
```json
{"anti_patterns": [...], "suggestions": [...], "score": 65, "summary": "..."}
```

### POST /api/v1/pipelines/validate
```json
{"yaml_content": "..."}
```

### POST /api/v1/pipelines/generate
```json
{"requirements": "Node.js app with tests and Docker", "platform": "github_actions"}
```

---

## Logs & RAG

### POST /api/v1/logs/
Create a log entry.

### GET /api/v1/logs/project/{id}
List logs for a project. Optional query param: `level=ERROR`

### POST /api/v1/logs/upload
Upload log text for RAG indexing.

### POST /api/v1/logs/upload-file
Upload a log file (multipart form data).

### POST /api/v1/logs/rag/query
```json
{"question": "How to fix CrashLoopBackOff?", "k": 5}
```

**Response:**
```json
{"answer": "...", "sources": [...], "confidence": 0.85, "query": "..."}
```

### GET /api/v1/logs/rag/stats
Vector store statistics.

### POST /api/v1/logs/rag/index-docs
Index the built-in DevOps knowledge base.

---

## Infrastructure

### POST /api/v1/infra/generate
```json
{"config_type": "docker_compose", "app_description": "Python app with PostgreSQL"}
```

### POST /api/v1/infra/execute
```json
{"operation": "plan", "config_type": "kubernetes"}
```

### GET /api/v1/infra/status

---

## Health

### GET /health
```json
{"status": "healthy", "version": "1.0.0", "services": {"database": {"status": "healthy"}, "redis": {"status": "healthy"}, "ollama": {"status": "healthy"}, "faiss": {"status": "healthy"}}}
```
