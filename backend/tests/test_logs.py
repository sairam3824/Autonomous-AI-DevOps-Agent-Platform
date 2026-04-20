import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_log_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.post(
        "/api/v1/logs/",
        headers=auth_headers,
        json={
            "source": "app",
            "level": "ERROR",
            "content": "Unauthorized log write attempt",
            "project_id": other_project.id,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_logs_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.get(
        f"/api/v1/logs/project/{other_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_logs_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.post(
        "/api/v1/logs/upload",
        headers=auth_headers,
        json={
            "content": "2024-01-01 ERROR unauthorized project upload",
            "source": "manual-upload",
            "project_id": other_project.id,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_file_persists_log_entry(async_client: AsyncClient, auth_headers, test_project):
    file_content = b"2024-01-01 ERROR CrashLoopBackOff detected in web pod"
    response = await async_client.post(
        "/api/v1/logs/upload-file",
        headers=auth_headers,
        files={"file": ("app.log", file_content, "text/plain")},
        data={"project_id": str(test_project.id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["chunks_indexed"] >= 1
    assert data["source"] == "app.log"

    list_response = await async_client.get(
        f"/api/v1/logs/project/{test_project.id}",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    logs = list_response.json()
    assert any(log["source"] == "app.log" and log["indexed"] is True for log in logs)


@pytest.mark.asyncio
async def test_rag_query_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.post(
        "/api/v1/logs/rag/query",
        headers=auth_headers,
        json={"question": "How to fix CrashLoopBackOff?", "k": 5, "project_id": other_project.id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rag_stats_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.get(
        "/api/v1/logs/rag/stats",
        headers=auth_headers,
        params={"project_id": other_project.id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_index_docs_requires_owned_project(async_client: AsyncClient, auth_headers, other_project):
    response = await async_client.post(
        "/api/v1/logs/rag/index-docs",
        headers=auth_headers,
        params={"project_id": other_project.id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rag_query_is_scoped_to_selected_project(
    async_client: AsyncClient,
    auth_headers,
    test_project,
    second_test_project,
):
    await async_client.post(
        "/api/v1/logs/upload",
        headers=auth_headers,
        json={
            "content": "ALPHA_ERROR unique-token-alpha remediation alpha",
            "source": "alpha-log",
            "project_id": test_project.id,
        },
    )
    await async_client.post(
        "/api/v1/logs/upload",
        headers=auth_headers,
        json={
            "content": "BETA_ERROR unique-token-beta remediation beta",
            "source": "beta-log",
            "project_id": second_test_project.id,
        },
    )

    response = await async_client.post(
        "/api/v1/logs/rag/query",
        headers=auth_headers,
        json={"question": "unique-token-alpha", "k": 5, "project_id": test_project.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(source["source"] == "alpha-log" for source in data["sources"])
