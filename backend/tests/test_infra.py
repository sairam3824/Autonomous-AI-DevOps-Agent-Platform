import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_docker_compose(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/infra/generate",
        headers=auth_headers,
        json={
            "config_type": "docker_compose",
            "app_description": "Python web application with PostgreSQL and Redis",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["config_type"] == "docker_compose"
    assert len(data["output"]) > 50


@pytest.mark.asyncio
async def test_generate_kubernetes(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/infra/generate",
        headers=auth_headers,
        json={
            "config_type": "kubernetes",
            "app_description": "Node.js microservice",
            "options": {"name": "web-api", "port": 3000, "replicas": 3},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Deployment" in data["output"]


@pytest.mark.asyncio
async def test_generate_terraform(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/infra/generate",
        headers=auth_headers,
        json={
            "config_type": "terraform",
            "app_description": "Web application deployment",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "terraform" in data["output"].lower()


@pytest.mark.asyncio
async def test_infra_status(async_client: AsyncClient, auth_headers):
    response = await async_client.get("/api/v1/infra/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "supported_configs" in data
    assert "agents" in data


@pytest.mark.asyncio
async def test_execute_infra_status(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/infra/execute",
        headers=auth_headers,
        json={"operation": "status", "config_type": "docker_compose"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
