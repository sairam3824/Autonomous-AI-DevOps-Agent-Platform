import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_run_heal_agent(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/agents/run",
        headers=auth_headers,
        json={
            "agent_type": "heal",
            "input_data": {
                "logs": "Pod web-app-xyz is in CrashLoopBackOff state",
                "context": {"pod_name": "web-app-xyz", "namespace": "production"},
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "heal"
    assert data["status"] in ("completed", "failed")


@pytest.mark.asyncio
async def test_run_pipeline_agent(async_client: AsyncClient, auth_headers):
    yaml_content = """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm test
"""
    response = await async_client.post(
        "/api/v1/agents/run",
        headers=auth_headers,
        json={
            "agent_type": "pipeline",
            "input_data": {"action": "analyze", "yaml_content": yaml_content},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "pipeline"


@pytest.mark.asyncio
async def test_run_infra_agent(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/agents/run",
        headers=auth_headers,
        json={
            "agent_type": "infra",
            "input_data": {
                "config_type": "docker_compose",
                "app_description": "Python FastAPI web application with PostgreSQL database",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "infra"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_run_invalid_agent_type(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/agents/run",
        headers=auth_headers,
        json={
            "agent_type": "invalid",
            "input_data": {},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_run_agent_unauthorized(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/agents/run",
        json={"agent_type": "heal", "input_data": {"logs": "test"}},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auto_diagnose_marks_failure_on_invalid_input(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/agents/auto-diagnose",
        headers=auth_headers,
        json={"agent_type": "heal", "input_data": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["steps"][0]["success"] is False


@pytest.mark.asyncio
async def test_run_agent_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.post(
        "/api/v1/agents/run",
        headers=auth_headers,
        json={
            "agent_type": "heal",
            "project_id": other_project.id,
            "input_data": {"logs": "CrashLoopBackOff"},
        },
    )
    assert response.status_code == 404
