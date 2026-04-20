from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_agent import PipelineAgent
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.models import Pipeline, Project, User
from app.schemas.schemas import (
    PipelineAnalyzeRequest,
    PipelineAnalyzeResponse,
    PipelineCreate,
    PipelineGenerateRequest,
    PipelineResponse,
    PipelineValidateRequest,
    PipelineValidateResponse,
)

router = APIRouter(prefix="/api/v1/pipelines", tags=["Pipelines"])
pipeline_agent = PipelineAgent()


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


@router.post("/", response_model=PipelineResponse, status_code=201)
async def create_pipeline(
    data: PipelineCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(data.project_id, current_user, db)
    pipeline = Pipeline(
        name=data.name,
        platform=data.platform,
        yaml_content=data.yaml_content,
        project_id=data.project_id,
    )
    db.add(pipeline)
    await db.flush()
    await db.refresh(pipeline)
    return PipelineResponse.model_validate(pipeline)


@router.get("/project/{project_id}", response_model=list[PipelineResponse])
async def list_pipelines(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(project_id, current_user, db)
    result = await db.execute(
        select(Pipeline).where(Pipeline.project_id == project_id).order_by(Pipeline.created_at.desc())
    )
    pipelines = result.scalars().all()
    return [PipelineResponse.model_validate(p) for p in pipelines]


@router.post("/analyze", response_model=PipelineAnalyzeResponse)
async def analyze_pipeline(
    request: PipelineAnalyzeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await pipeline_agent.run({
        "action": "analyze",
        "yaml_content": request.yaml_content,
        "platform": request.platform,
    })

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Analysis failed")

    output = result.output
    return PipelineAnalyzeResponse(
        anti_patterns=output.get("anti_patterns", []),
        suggestions=output.get("suggestions", []),
        optimized_yaml=output.get("optimized_yaml"),
        score=output.get("score", 0),
        summary=output.get("summary", ""),
    )


@router.post("/validate", response_model=PipelineValidateResponse)
async def validate_pipeline(
    request: PipelineValidateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await pipeline_agent.run({
        "action": "validate",
        "yaml_content": request.yaml_content,
    })

    output = result.output
    return PipelineValidateResponse(
        valid=output.get("valid", False),
        errors=output.get("errors", []),
    )


@router.post("/generate")
async def generate_pipeline(
    request: PipelineGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await pipeline_agent.run({
        "action": "generate",
        "requirements": request.requirements,
        "platform": request.platform,
    })

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Generation failed")

    return {
        "yaml_content": result.output.get("yaml_content", ""),
        "platform": result.output.get("platform", request.platform),
        "source": result.output.get("source", "template"),
    }
