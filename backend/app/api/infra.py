from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.agents.infra_agent import InfraAgent
from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.models import User
from app.schemas.schemas import InfraExecuteRequest, InfraGenerateRequest, InfraResponse

router = APIRouter(prefix="/api/v1/infra", tags=["Infrastructure"])
settings = get_settings()
infra_agent = InfraAgent()


@router.post("/generate", response_model=InfraResponse)
async def generate_infra(
    request: InfraGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await infra_agent.run({
        "config_type": request.config_type,
        "app_description": request.app_description,
        "options": request.options or {},
    })

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Generation failed")

    return InfraResponse(
        success=True,
        config_type=request.config_type,
        output=result.output.get("generated_config", ""),
        generated_files={f"{request.config_type}.yaml": result.output.get("generated_config", "")},
        metadata={"source": result.output.get("source", "unknown"), "execution_time_ms": result.execution_time_ms},
    )


@router.post("/execute", response_model=InfraResponse)
async def execute_infra(
    request: InfraExecuteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if request.operation == "status":
        return InfraResponse(
            success=True,
            config_type=request.config_type,
            output="Infrastructure status check completed",
            metadata={"operation": "status"},
        )

    if request.operation == "generate":
        result = await infra_agent.run({
            "config_type": request.config_type,
            "app_description": request.config_data.get("description", "web application") if request.config_data else "web application",
            "options": request.config_data or {},
        })

        return InfraResponse(
            success=result.success,
            config_type=request.config_type,
            output=result.output.get("generated_config", str(result.output)),
            metadata={"operation": request.operation, "execution_time_ms": result.execution_time_ms},
        )

    if request.operation in ("plan", "apply"):
        return InfraResponse(
            success=True,
            config_type=request.config_type,
            output=f"Operation '{request.operation}' completed (dry-run mode - no actual infrastructure changes)",
            metadata={"operation": request.operation, "dry_run": True},
        )

    raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")


@router.get("/status")
async def infra_status(current_user: Annotated[User, Depends(get_current_user)]):
    ollama_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                ollama_status = f"healthy ({len(models)} models)"
            else:
                ollama_status = "unhealthy"
    except Exception:
        ollama_status = "unreachable"

    return {
        "ollama": ollama_status,
        "supported_configs": ["docker_compose", "kubernetes", "terraform"],
        "agents": ["infra", "pipeline", "heal"],
    }
