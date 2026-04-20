from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, get_password_hash
from app.db.database import get_db
from app.main import app
from app.ml.vector_store import vector_store
from app.models.models import Base, Project, User


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": str(test_user.id), "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def disable_transformer_embedder(monkeypatch: pytest.MonkeyPatch):
    vector_store.clear()
    vector_store._embedder = None
    monkeypatch.setattr(vector_store, "_load_embedder", lambda: None)
    yield
    vector_store.clear()


@pytest_asyncio.fixture
async def test_project(test_db: AsyncSession, test_user: User) -> Project:
    project = Project(
        name="Test Project",
        description="Owned by the authenticated test user",
        repo_url="https://github.com/example/test-project",
        user_id=test_user.id,
    )
    test_db.add(project)
    await test_db.flush()
    await test_db.refresh(project)
    return project


@pytest_asyncio.fixture
async def other_user(test_db: AsyncSession) -> User:
    user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password=get_password_hash("otherpass123"),
        role="engineer",
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_project(test_db: AsyncSession, other_user: User) -> Project:
    project = Project(
        name="Other User Project",
        description="Owned by another user",
        repo_url="https://github.com/example/other-project",
        user_id=other_user.id,
    )
    test_db.add(project)
    await test_db.flush()
    await test_db.refresh(project)
    return project


@pytest_asyncio.fixture
async def second_test_project(test_db: AsyncSession, test_user: User) -> Project:
    project = Project(
        name="Second Test Project",
        description="Another project owned by the authenticated test user",
        repo_url="https://github.com/example/second-test-project",
        user_id=test_user.id,
    )
    test_db.add(project)
    await test_db.flush()
    await test_db.refresh(project)
    return project
