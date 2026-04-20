from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    normalized = value.lower().strip()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise ValueError("Invalid email address")
    return normalized


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, examples=["user@example.com"])
    username: str = Field(..., min_length=3, max_length=100, examples=["johndoe"])
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _normalize_email(v)


class UserLogin(BaseModel):
    email: str = Field(..., examples=["demo@devops.ai"])
    password: str = Field(..., examples=["demo1234"])

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _normalize_email(v)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, examples=["E-Commerce Platform"])
    description: Optional[str] = Field(None, max_length=2000)
    repo_url: Optional[str] = Field(None, max_length=500)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    repo_url: Optional[str] = Field(None, max_length=500)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    repo_url: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., pattern="^(infra|pipeline|heal)$", examples=["heal"])
    input_data: dict[str, Any] = Field(..., examples=[{"logs": "CrashLoopBackOff in pod web-app-xyz"}])
    project_id: Optional[int] = None


class AgentRunResponse(BaseModel):
    id: int
    agent_type: str
    status: str
    input_data: Optional[dict[str, Any]]
    output_data: Optional[dict[str, Any]]
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentMultiRunRequest(BaseModel):
    agents: list[AgentRunRequest] = Field(..., min_length=1, max_length=5)
    mode: str = Field("sequential", pattern="^(sequential|parallel)$")
    project_id: Optional[int] = None


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    platform: str = Field(..., pattern="^(github_actions|jenkins|gitlab_ci)$")
    yaml_content: str = Field(..., min_length=1)
    project_id: int


class PipelineResponse(BaseModel):
    id: int
    name: str
    platform: str
    yaml_content: str
    analysis_result: Optional[dict[str, Any]]
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineAnalyzeRequest(BaseModel):
    yaml_content: str = Field(..., min_length=10)
    platform: str = Field("github_actions", pattern="^(github_actions|jenkins|gitlab_ci)$")


class PipelineAnalyzeResponse(BaseModel):
    anti_patterns: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]
    optimized_yaml: Optional[str]
    score: int = Field(..., ge=0, le=100)
    summary: str


class PipelineGenerateRequest(BaseModel):
    requirements: str = Field(..., min_length=10, examples=["Node.js app with tests, Docker build, and deploy to K8s"])
    platform: str = Field("github_actions", pattern="^(github_actions|jenkins|gitlab_ci)$")


class PipelineValidateRequest(BaseModel):
    yaml_content: str = Field(..., min_length=1)


class PipelineValidateResponse(BaseModel):
    valid: bool
    errors: list[str]


class LogCreate(BaseModel):
    source: str = Field(..., min_length=1, max_length=100)
    level: str = Field("INFO", pattern="^(DEBUG|INFO|WARN|ERROR|FATAL)$")
    content: str = Field(..., min_length=1)
    metadata_: Optional[dict[str, Any]] = Field(None, alias="metadata")
    project_id: int


class LogResponse(BaseModel):
    id: int
    source: str
    level: str
    content: str
    metadata_: Optional[dict[str, Any]] = Field(None, alias="metadata")
    project_id: int
    indexed: bool
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class LogUploadRequest(BaseModel):
    content: str = Field(..., min_length=10)
    source: str = Field("upload", max_length=100)
    project_id: int


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000, examples=["How to fix CrashLoopBackOff in Kubernetes?"])
    k: int = Field(5, ge=1, le=20)
    project_id: int


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    confidence: float = Field(..., ge=0.0, le=1.0)
    query: str


class RAGStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    index_size_bytes: int
    embedding_model: str


class InfraGenerateRequest(BaseModel):
    config_type: str = Field(..., pattern="^(docker_compose|kubernetes|terraform)$")
    app_description: str = Field(..., min_length=10, examples=["Python FastAPI app with PostgreSQL and Redis"])
    options: Optional[dict[str, Any]] = None


class InfraExecuteRequest(BaseModel):
    operation: str = Field(..., pattern="^(plan|apply|status|generate)$")
    config_type: str = Field(..., pattern="^(docker_compose|kubernetes|terraform)$")
    config_data: Optional[dict[str, Any]] = None


class InfraResponse(BaseModel):
    success: bool
    config_type: str
    output: str
    generated_files: Optional[dict[str, str]] = None
    metadata: Optional[dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, dict[str, Any]]
