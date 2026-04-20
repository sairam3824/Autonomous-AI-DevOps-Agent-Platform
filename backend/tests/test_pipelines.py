import pytest
from httpx import AsyncClient


SAMPLE_YAML = """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm test
      - run: npm run build
"""


@pytest.mark.asyncio
async def test_analyze_pipeline(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/pipelines/analyze",
        headers=auth_headers,
        json={"yaml_content": SAMPLE_YAML, "platform": "github_actions"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "anti_patterns" in data
    assert "suggestions" in data
    assert isinstance(data["score"], int)
    assert 0 <= data["score"] <= 100


@pytest.mark.asyncio
async def test_validate_pipeline_valid(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/pipelines/validate",
        headers=auth_headers,
        json={"yaml_content": SAMPLE_YAML},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_validate_pipeline_invalid(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/pipelines/validate",
        headers=auth_headers,
        json={"yaml_content": "invalid: yaml: [broken"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_generate_pipeline(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/pipelines/generate",
        headers=auth_headers,
        json={
            "requirements": "Node.js application with testing and Docker build",
            "platform": "github_actions",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "yaml_content" in data
    assert len(data["yaml_content"]) > 50


@pytest.mark.asyncio
async def test_create_pipeline_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.post(
        "/api/v1/pipelines/",
        headers=auth_headers,
        json={
            "name": "Unauthorized Pipeline",
            "platform": "github_actions",
            "yaml_content": SAMPLE_YAML,
            "project_id": other_project.id,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pipelines_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.get(
        f"/api/v1/pipelines/project/{other_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
