import asyncio
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.database import Base
from app.api.v1.dependencies import get_db  # the dependency we will override

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_catsi.db"  # or use ":memory:" but SQLite async with memory can be tricky, so use a file

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Provide a session
    async with TestSessionLocal() as session:
        yield session
    # Drop tables after test (optional, but clean)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


from app.main import app

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

from app.schemas.user import UserCreate

@pytest_asyncio.fixture(scope="function")
async def registered_user(client, db_session):
    user_data = {"username": "testuser", "email": "test@example.com", "password": "secret123"}
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data  # return the plain data for login