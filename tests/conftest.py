import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from main import app
from db.base import Base
from db.session import get_async_db

TEST_DATA_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATA_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


async def override_get_db():
    """Override the async database dependency with the test session."""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Override the database dependency
app.dependency_overrides[get_async_db] = override_get_db


@pytest_asyncio.fixture(name="db", scope="function")
async def db_fixture():
    """Test db session"""
    # Create all tables before running any test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        session = TestingAsyncSessionLocal()
        yield session
    finally:
        await session.close()
        # Drop all the tables after test completed
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="client", scope="function")
def client_fixture():
    """Test client for fastapi app"""
    return TestClient(app)


@pytest_asyncio.fixture(name="async_client", scope="function")
async def async_client_fixture() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the fastapi app"""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="https://test"
    ) as async_client:
        yield async_client


@pytest.fixture(autouse=True)
def mock_auth(request):
    try:
        from utils.security import require_api_key

        if request.node.get_closest_marker("real_auth"):
            yield
            return

        def mock_require_api_key():
            return "xxxxxxx"

        app.dependency_overrides[require_api_key] = mock_require_api_key
        yield

        if require_api_key in app.dependency_overrides:
            del app.dependency_overrides[require_api_key]
    except ImportError:
        yield


# -----------------------------------------------------------
# --------------------  Mock Data  --------------------------


@pytest.fixture
def mock_language_sample():
    return {
        "id": 1,
        "name": "C",
        "version": "GCC 13.3.0",
        "source_file": "main.c",
        "compile_cmd": "gcc -o main main.c -lm",
        "run_cmd": "./main",
        "is_archived": False,
    }


@pytest.fixture
def mock_language_samples():
    return [
        {
            "id": 1,
            "name": "C",
            "version": "GCC 13.3.0",
            "source_file": "main.c",
            "compile_cmd": "gcc -o main main.c -lm",
            "run_cmd": "./main",
            "is_archived": False,
        }
    ]


@pytest.fixture
def mock_submission_sample():
    return {
        "token": str(uuid.uuid4()),
        "source_code": "print('Hello world')",
        "language_id": 3,
        "status": "Queued",
        "cpu_time_limit": 1,
        "cpu_extra_time": 1,
        "wall_time_limit": 1,
        "memory_limit": 10 * 1024,
        "stack_limit": 10 * 1024,
        "max_file_size": 1024,
        "max_processes_and_or_threads": 1,
        "limit_per_process_and_thread_cpu_time_usages": False,
        "limit_per_process_and_thread_memory_usages": False,
    }


@pytest.fixture
def mock_submission_samples():
    return [
        {
            "token": str(uuid.uuid4()),
            "source_code": "print('Hello world')",
            "language_id": 3,
            "status": "Queued",
            "cpu_time_limit": 1,
            "cpu_extra_time": 1,
            "wall_time_limit": 1,
            "memory_limit": 10 * 1024,
            "stack_limit": 10 * 1024,
            "max_file_size": 1024,
            "max_processes_and_or_threads": 1,
            "limit_per_process_and_thread_cpu_time_usages": False,
            "limit_per_process_and_thread_memory_usages": False,
        },
        {
            "token": str(uuid.uuid4()),
            "source_code": "cout << 'Hello world!'",
            "language_id": 2,
            "status": "Processing",
            "cpu_time_limit": 1,
            "cpu_extra_time": 1,
            "wall_time_limit": 1,
            "memory_limit": 10 * 1024,
            "stack_limit": 10 * 1024,
            "max_file_size": 1024,
            "max_processes_and_or_threads": 1,
            "limit_per_process_and_thread_cpu_time_usages": False,
            "limit_per_process_and_thread_memory_usages": False,
        },
        {
            "token": str(uuid.uuid4()),
            "source_code": "print('Hello world')",
            "language_id": 3,
            "status": "Queued",
            "cpu_time_limit": 1,
            "cpu_extra_time": 1,
            "wall_time_limit": 1,
            "memory_limit": 10 * 1024,
            "stack_limit": 10 * 1024,
            "max_file_size": 1024,
            "max_processes_and_or_threads": 1,
            "limit_per_process_and_thread_cpu_time_usages": False,
            "limit_per_process_and_thread_memory_usages": False,
        },
        {
            "token": str(uuid.uuid4()),
            "source_code": "cout << 'Hello world!'",
            "language_id": 2,
            "status": "Processing",
            "cpu_time_limit": 1,
            "cpu_extra_time": 1,
            "wall_time_limit": 1,
            "memory_limit": 10 * 1024,
            "stack_limit": 10 * 1024,
            "max_file_size": 1024,
            "max_processes_and_or_threads": 1,
            "limit_per_process_and_thread_cpu_time_usages": False,
            "limit_per_process_and_thread_memory_usages": False,
        },
    ]
