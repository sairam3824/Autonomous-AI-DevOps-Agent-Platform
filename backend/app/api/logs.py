from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.ml.rag_service import rag_service
from app.ml.vector_store import vector_store
from app.models.models import LogEntry, Project, User
from app.schemas.schemas import (
    LogCreate,
    LogResponse,
    LogUploadRequest,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatsResponse,
)

router = APIRouter(prefix="/api/v1/logs", tags=["Logs & RAG"])


async def _ensure_project_access(
    project_id: int,
    current_user: User,
    db: AsyncSession,
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _serialize_log(log_entry: LogEntry) -> LogResponse:
    return LogResponse.model_validate(
        {
            "id": log_entry.id,
            "source": log_entry.source,
            "level": log_entry.level,
            "content": log_entry.content,
            "metadata": log_entry.metadata_,
            "project_id": log_entry.project_id,
            "indexed": log_entry.indexed,
            "created_at": log_entry.created_at,
        }
    )


@router.post("/", response_model=LogResponse, status_code=201)
async def create_log(
    data: LogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(data.project_id, current_user, db)
    log_entry = LogEntry(
        source=data.source,
        level=data.level,
        content=data.content,
        metadata_=data.metadata_,
        project_id=data.project_id,
    )
    db.add(log_entry)
    await db.flush()
    await db.refresh(log_entry)
    return _serialize_log(log_entry)


@router.get("/project/{project_id}", response_model=list[LogResponse])
async def list_logs(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    level: str | None = None,
    limit: int = 100,
):
    await _ensure_project_access(project_id, current_user, db)
    query = select(LogEntry).where(LogEntry.project_id == project_id)
    if level:
        query = query.where(LogEntry.level == level)
    query = query.order_by(LogEntry.created_at.desc()).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()
    return [_serialize_log(log) for log in logs]


@router.post("/upload")
async def upload_logs(
    data: LogUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(data.project_id, current_user, db)
    log_entry = LogEntry(
        source=data.source,
        level="INFO",
        content=data.content,
        project_id=data.project_id,
        indexed=True,
    )
    db.add(log_entry)
    await db.flush()

    chunks_added = rag_service.index_documents(
        [data.content],
        source=data.source,
        extra_metadata={"project_id": data.project_id, "document_type": "log"},
    )

    return {
        "message": "Logs uploaded and indexed successfully",
        "chunks_indexed": chunks_added,
        "source": data.source,
    }


@router.post("/upload-file")
async def upload_log_file(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: int = Form(...),
    source: str | None = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    await _ensure_project_access(project_id, current_user, db)

    content = await file.read()
    text = content.decode("utf-8", errors="replace")

    if len(text) < 10:
        raise HTTPException(status_code=400, detail="File is too small or empty")

    log_source = source or file.filename
    log_entry = LogEntry(
        source=log_source,
        level="INFO",
        content=text,
        project_id=project_id,
        indexed=True,
    )
    db.add(log_entry)
    await db.flush()

    chunks_added = rag_service.index_documents(
        [text],
        source=log_source,
        extra_metadata={"project_id": project_id, "document_type": "log"},
    )

    return {
        "message": f"File '{file.filename}' uploaded and indexed",
        "file_size_bytes": len(content),
        "chunks_indexed": chunks_added,
        "source": log_source,
    }


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(request.project_id, current_user, db)
    result = await rag_service.query(
        request.question,
        k=request.k,
        filters={"project_id": request.project_id},
    )
    return RAGQueryResponse(**result)


@router.get("/rag/stats", response_model=RAGStatsResponse)
async def rag_stats(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(project_id, current_user, db)
    stats = vector_store.get_stats()
    filtered_chunks = sum(
        1 for metadata in vector_store._metadatas if metadata.get("project_id") == project_id
    )
    stats["total_documents"] = filtered_chunks
    stats["total_chunks"] = filtered_chunks
    return RAGStatsResponse(**stats)


@router.post("/rag/index-docs")
async def index_devops_docs(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(project_id, current_user, db)
    docs_path = Path(__file__).parent.parent.parent / "sample_data" / "devops_knowledge.md"

    if not docs_path.exists():
        raise HTTPException(status_code=404, detail="Sample DevOps docs not found")

    content = docs_path.read_text(encoding="utf-8")
    chunks_added = rag_service.index_documents(
        [content],
        source="devops_knowledge_base",
        extra_metadata={"project_id": project_id, "document_type": "knowledge_base"},
    )

    return {
        "message": "DevOps knowledge base indexed successfully",
        "chunks_indexed": chunks_added,
        "source": "devops_knowledge_base",
    }
