import hashlib
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import orchestrator
from app.core.security import get_current_user, get_user_from_token
from app.db.database import async_session_maker, get_db
from app.db.redis_cache import get_redis_cache, RedisCache
from app.models.models import AgentRun, Project, User
from app.schemas.schemas import AgentMultiRunRequest, AgentRunRequest, AgentRunResponse

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


async def _ensure_project_access(
    project_id: int | None,
    current_user: User,
    db: AsyncSession,
) -> Project | None:
    if project_id is None:
        return None

    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[RedisCache, Depends(get_redis_cache)],
):
    await _ensure_project_access(request.project_id, current_user, db)

    cache_payload = json.dumps(
        {"input_data": request.input_data, "project_id": request.project_id},
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    cache_digest = hashlib.sha256(cache_payload.encode("utf-8")).hexdigest()
    cache_key = f"agent:{current_user.id}:{request.agent_type}:{cache_digest}"
    cached = await cache.get(cache_key)
    if cached:
        agent_run = AgentRun(
            agent_type=request.agent_type,
            status="completed",
            input_data=request.input_data,
            output_data=cached,
            execution_time_ms=0,
            user_id=current_user.id,
            project_id=request.project_id,
        )
        db.add(agent_run)
        await db.flush()
        await db.refresh(agent_run)
        return AgentRunResponse.model_validate(agent_run)

    agent_run = AgentRun(
        agent_type=request.agent_type,
        status="running",
        input_data=request.input_data,
        user_id=current_user.id,
        project_id=request.project_id,
    )
    db.add(agent_run)
    await db.flush()
    await db.refresh(agent_run)

    result = await orchestrator.run_single(request.agent_type, request.input_data)

    agent_run.status = "completed" if result.success else "failed"
    agent_run.output_data = result.output
    agent_run.execution_time_ms = result.execution_time_ms
    agent_run.error_message = result.error
    await db.flush()
    await db.refresh(agent_run)

    if result.success:
        await cache.set(cache_key, result.output, ttl=300)

    return AgentRunResponse.model_validate(agent_run)


@router.post("/multi-run")
async def multi_run(
    request: AgentMultiRunRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(request.project_id, current_user, db)

    agents_config = [
        {"agent_type": a.agent_type, "input_data": a.input_data}
        for a in request.agents
    ]

    results = await orchestrator.run_multi(agents_config, mode=request.mode)

    responses = []
    for i, result in enumerate(results):
        agent_run = AgentRun(
            agent_type=agents_config[i]["agent_type"],
            status="completed" if result.success else "failed",
            input_data=agents_config[i]["input_data"],
            output_data=result.output,
            execution_time_ms=result.execution_time_ms,
            error_message=result.error,
            user_id=current_user.id,
            project_id=request.project_id,
        )
        db.add(agent_run)
        await db.flush()
        await db.refresh(agent_run)
        responses.append(AgentRunResponse.model_validate(agent_run))

    return {"results": responses, "mode": request.mode, "total": len(responses)}


@router.post("/auto-diagnose")
async def auto_diagnose(
    request: AgentRunRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _ensure_project_access(request.project_id, current_user, db)

    result = await orchestrator.auto_diagnose(request.input_data)

    agent_run = AgentRun(
        agent_type="orchestrator",
        status="completed" if result.get("success") else "failed",
        input_data=request.input_data,
        output_data=result,
        execution_time_ms=result.get("total_execution_time_ms", 0),
        user_id=current_user.id,
        project_id=request.project_id,
    )
    db.add(agent_run)
    await db.flush()

    return result


@router.websocket("/ws/stream/{agent_type}")
async def agent_stream(websocket: WebSocket, agent_type: str):
    await websocket.accept()

    try:
        token = websocket.query_params.get("token")
        auth_header = websocket.headers.get("authorization", "")
        if not token and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        async with async_session_maker() as session:
            await get_user_from_token(token, session)

        data = await websocket.receive_json()
        input_data = data.get("input_data", {})

        async def send_event(event: dict[str, Any]) -> None:
            await websocket.send_json(event)

        result = await orchestrator.run_single(agent_type, input_data, callback=send_event)

        await websocket.send_json({
            "type": "final_result",
            "success": result.success,
            "output": result.output,
            "execution_time_ms": result.execution_time_ms,
        })

    except WebSocketDisconnect:
        pass
    except HTTPException as e:
        try:
            await websocket.send_json({"type": "error", "message": e.detail})
        except Exception:
            pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
