import sys
from pathlib import Path

# Add the parent directory to sys.path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from main import app
from db.base import Base

TEST_DATA_URL = "sqlite:///:memory"

test_engine = create_engine(
    TEST_DATA_URL,
    connect_args={"check_same_thread": False},
    pool=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    """This will override the existing database session"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides["get_async_db"] = override_get_db()


@pytest.fixture(name="db", scope="function")
def db_fixture():
    """Test db session"""
    # Create all tables before running any test
    Base.metadata.create_all(bind=test_engine)

    try:
        session = TestingSessionLocal()
        yield session
    finally:
        session.close()
        # Drop all the tables after test completed
        Base.metadata.drop_all()


@pytest.fixture(name="client", scope="function")
def client_fixture():
    """Test client for fastapi app"""
    return TestClient(app)
