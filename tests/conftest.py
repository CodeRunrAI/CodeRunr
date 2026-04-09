import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db.base import Base
from db.session import get_async_db

TEST_DB_PATH = Path(__file__).resolve().parent.parent / "tmp"
TEST_DB_PATH.mkdir(exist_ok=True)

TEST_DB_PATH = TEST_DB_PATH / "test.sqlite3"
TEST_DATA_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
TEST_SYNC_DATA_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"

test_engine = create_async_engine(
    TEST_DATA_URL,
    connect_args={"check_same_thread": False},
)
test_sync_engine = create_engine(
    TEST_SYNC_DATA_URL,
    connect_args={"check_same_thread": False},
)

TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)
TestingSyncSessionLocal = sessionmaker(
    bind=test_sync_engine,
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


@pytest.fixture(autouse=True)
def setup_database():
    """Create and clean the shared test database for each test."""
    Base.metadata.drop_all(bind=test_sync_engine)
    Base.metadata.create_all(bind=test_sync_engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=test_sync_engine)


@pytest_asyncio.fixture(name="db", scope="function")
async def db_fixture():
    """Async test db session"""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(name="sync_db", scope="function")
def sync_db_fixture():
    """Sync test db session"""
    session = TestingSyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


event.listen(test_sync_engine, "connect", _enable_sqlite_foreign_keys)
event.listen(test_engine.sync_engine, "connect", _enable_sqlite_foreign_keys)


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
        },
        {
            "id": 2,
            "name": "C++",
            "version": "GCC 13.3.0",
            "source_file": "main.cpp",
            "compile_cmd": "g++ -o main main.cpp -std=c++17",
            "run_cmd": "./main",
            "is_archived": False,
        },
        {
            "id": 3,
            "name": "Python",
            "version": "3.12.3",
            "source_file": "main.py",
            "compile_cmd": "python3 -m py_compile main.py",
            "run_cmd": "python3 main.py",
            "is_archived": False,
        },
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
